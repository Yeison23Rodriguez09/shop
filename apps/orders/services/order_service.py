# apps/orders/services/order_service.py
"""
OrderService — toda la logica de negocio de ordenes, desacoplada de las vistas.

Responsabilidades:
  - Crear una orden desde el carrito (con stock atomico via select_for_update)
  - Cambiar estado con log automatico y reposicion de stock al cancelar
  - Confirmar pago (desde webhook o manual) en una transaccion atomica
  - Calcular totales
  - Validar stock antes de crear

Politica de stock:
  - Se DESCUENTA al crear la orden (first-to-checkout reserva).
  - Se REPONE al transitar a 'cancelled' o 'refunded' (idempotente).
  - select_for_update bloquea la fila del producto durante la operacion
    para evitar sobreventa en concurrencia.
"""
import logging
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from django.db.models import F

from apps.orders.models import Order, OrderItem, OrderLog
from apps.catalog.models import Product, ProductVariant

logger = logging.getLogger('orders')

# Estados que ya descontaron stock al momento de su creacion
# (toda orden creada por create_from_cart pasa por aqui).
STATES_WITH_STOCK_DECREMENTED = {
    'pending', 'paid', 'processing', 'shipped', 'delivered',
}
# Estados que devuelven el stock al inventario.
STATES_THAT_RESTORE_STOCK = {'cancelled', 'refunded'}


class OrderService:

    # ────────────────────────────────────────────────────────
    #  Creacion desde carrito (atomica)
    # ────────────────────────────────────────────────────────
    @staticmethod
    @transaction.atomic
    def create_from_cart(cart_service, user, address_data, payment_method='wompi'):
        """
        Crea una Order completa desde el CartService.

        Bloquea las filas de Product con select_for_update para que dos
        usuarios concurrentes no puedan crear dos ordenes para la misma
        unidad. Si el stock es insuficiente al validar dentro de la
        transaccion, se aborta.

        Lanza ValueError si el carrito esta vacio o stock insuficiente.
        """
        cart_items = cart_service.get_items()
        if not cart_items:
            raise ValueError('El carrito esta vacio.')

        # Lock estable: primero variantes (si las hay), luego productos sin variante.
        variant_ids = sorted({i['variant'].id for i in cart_items if i.get('variant')})
        product_ids = sorted({i['product'].id for i in cart_items if not i.get('variant')})

        locked_variants = {
            v.id: v for v in
            ProductVariant.objects.select_for_update()
                                  .select_related('product')
                                  .filter(id__in=variant_ids)
        } if variant_ids else {}
        locked_products = {
            p.id: p for p in
            Product.objects.select_for_update().filter(id__in=product_ids)
        } if product_ids else {}

        # Validar stock dentro del lock.
        for item in cart_items:
            qty = item['quantity']
            variant = item.get('variant')
            if variant is not None:
                v = locked_variants.get(variant.id)
                if v is None:
                    raise ValueError(f'Variante no encontrada: {variant.sku}.')
                if not v.is_active:
                    raise ValueError(f'Variante inactiva: {v.sku}.')
                if v.stock < qty:
                    raise ValueError(
                        f'Stock insuficiente para "{v.product.name}" ({v.color or "default"}). '
                        f'Disponible: {v.stock}, solicitado: {qty}.'
                    )
            else:
                p = locked_products.get(item['product'].id)
                if p is None:
                    raise ValueError(f'Producto no encontrado: {item["product"].name}.')
                if not p.is_active:
                    raise ValueError(f'Producto inactivo: {p.name}.')
                if p.stock < qty:
                    raise ValueError(
                        f'Stock insuficiente para "{p.name}". '
                        f'Disponible: {p.stock}, solicitado: {qty}.'
                    )

        subtotal = cart_service.get_total_price()
        shipping_cost = OrderService._calculate_shipping(subtotal, address_data.get('city', ''))
        total = subtotal + shipping_cost

        order = Order.objects.create(
            user=user,
            payment_method=payment_method,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            total_price=total,
            shipping_name=address_data.get('name', ''),
            shipping_phone=address_data.get('phone', ''),
            shipping_address=address_data.get('address', ''),
            shipping_city=address_data.get('city', ''),
            shipping_department=address_data.get('department', ''),
            shipping_postal_code=address_data.get('postal_code', ''),
            shipping_notes=address_data.get('notes', ''),
        )

        # Crear items + descontar stock atomicamente. Snapshot de variante.
        for item in cart_items:
            variant = item.get('variant')
            if variant is not None:
                v = locked_variants[variant.id]
                p = v.product
                OrderItem.objects.create(
                    order=order,
                    product=p, variant=v,
                    product_name=p.name,
                    product_model=p.model_number or '',
                    variant_color=v.color, variant_sku=v.sku,
                    quantity=item['quantity'],
                    unit_price=item['price'],
                )
                ProductVariant.objects.filter(pk=v.pk).update(stock=F('stock') - item['quantity'])
            else:
                p = locked_products[item['product'].id]
                OrderItem.objects.create(
                    order=order,
                    product=p,
                    product_name=p.name,
                    product_model=p.model_number or '',
                    quantity=item['quantity'],
                    unit_price=item['price'],
                )
                Product.objects.filter(pk=p.pk).update(stock=F('stock') - item['quantity'])

        OrderLog.objects.create(
            order=order,
            previous_status='',
            new_status='pending',
            changed_by=user,
            note='Orden creada desde el carrito.',
            source='system',
        )

        logger.info(
            'Orden creada | ref=%s | user=%s | total=%s | metodo=%s',
            order.reference, user.email, total, payment_method,
        )
        return order

    # ────────────────────────────────────────────────────────
    #  Cambio de estado (con reposicion de stock al cancelar)
    # ────────────────────────────────────────────────────────
    @staticmethod
    @transaction.atomic
    def change_status(order, new_status, changed_by=None, note='', source='admin'):
        """
        Cambia el estado de una orden y registra el log.

        Si la transicion va de un estado-con-stock-descontado a uno-que-repone,
        repone el stock de cada item de forma atomica. Idempotente: si el
        estado actual ya repone stock, no vuelve a sumar.

        Retorna: True si hubo cambio, False si ya tenia ese estado.
        """
        if order.status == new_status:
            return False

        old_status = order.status
        had_stock_decremented = old_status in STATES_WITH_STOCK_DECREMENTED
        will_restore_stock = (
            new_status in STATES_THAT_RESTORE_STOCK and had_stock_decremented
        )

        order.status = new_status
        update_fields = ['status']
        if new_status == 'paid' and not order.paid_at:
            order.paid_at = timezone.now()
            update_fields.append('paid_at')
        order.save(update_fields=update_fields)

        if will_restore_stock:
            OrderService._restore_stock(order)

        OrderLog.objects.create(
            order=order,
            previous_status=old_status,
            new_status=new_status,
            changed_by=changed_by,
            note=note,
            source=source,
        )

        logger.info(
            'Estado actualizado | ref=%s | %s -> %s | source=%s | restore_stock=%s',
            order.reference, old_status, new_status, source, will_restore_stock,
        )
        return True

    @staticmethod
    def _restore_stock(order):
        """Repone al inventario el stock de los items de una orden. Atomico.
        Si el item tiene variante, repone variant.stock; si no, product.stock."""
        for item in order.items.select_related('product', 'variant').all():
            if item.variant_id:
                ProductVariant.objects.filter(pk=item.variant_id).update(
                    stock=F('stock') + item.quantity
                )
                logger.info(
                    'Stock repuesto (variante) | order=%s | sku=%s | +%s',
                    order.reference, item.variant_sku, item.quantity,
                )
            else:
                Product.objects.filter(pk=item.product_id).update(
                    stock=F('stock') + item.quantity
                )
                logger.info(
                    'Stock repuesto | order=%s | producto=%s | +%s',
                    order.reference, item.product_name, item.quantity,
                )

    # ────────────────────────────────────────────────────────
    #  Confirmacion de pago (llamada desde webhook)
    # ────────────────────────────────────────────────────────
    @staticmethod
    @transaction.atomic
    def confirm_payment(order_reference, payment_id, gateway_name,
                        gateway_amount=None, gateway_currency='COP'):
        """
        Marca la orden como pagada. Llamada desde los webhooks.

        gateway_amount: OBLIGATORIO. Debe coincidir con order.total_price.
        Si es None o no coincide, el pago se rechaza (fail-closed). Esto
        previene que un webhook spoofeado o una integracion incompleta
        confirme un pago sin validar el monto.

        Idempotente: si la orden ya esta pagada, retorna sin cambios.

        Retorna: la Order actualizada o None si no se encontro / monto invalido.
        """
        try:
            # select_for_update para evitar dos webhooks simultaneos.
            order = Order.objects.select_for_update().get(reference=order_reference)
        except Order.DoesNotExist:
            logger.warning('Webhook pago: referencia no encontrada — %s', order_reference)
            return None

        if order.is_paid:
            logger.info('Webhook: orden %s ya estaba pagada, se ignora.', order_reference)
            return order

        # Fail-closed: sin monto no se puede validar contra el total → rechazar.
        if gateway_amount is None:
            logger.error(
                'Webhook %s: SIN MONTO para orden %s — RECHAZADO (fail-closed).',
                gateway_name, order_reference,
            )
            return None

        # Validacion de monto contra la pasarela.
        if gateway_amount is not None:
            try:
                gateway_amount_dec = Decimal(str(gateway_amount))
            except Exception:
                logger.error(
                    'Webhook %s: monto invalido recibido (%r) para orden %s.',
                    gateway_name, gateway_amount, order_reference,
                )
                return None
            if gateway_amount_dec != order.total_price:
                logger.error(
                    'Webhook %s: MONTO MISMATCH orden=%s esperado=%s recibido=%s — RECHAZADO.',
                    gateway_name, order_reference, order.total_price, gateway_amount_dec,
                )
                return None

        order.payment_id = payment_id
        order.save(update_fields=['payment_id'])

        OrderService.change_status(
            order,
            new_status='paid',
            note=f'Pago confirmado por {gateway_name}. ID transaccion: {payment_id}',
            source=f'webhook_{gateway_name}',
        )

        # Email asincrono — best effort.
        try:
            from apps.orders.tasks import send_order_confirmation_email
            send_order_confirmation_email.delay(order.id)
        except Exception:
            logger.warning('No se pudo encolar email de confirmacion para orden %s', order.id)

        return order

    # ────────────────────────────────────────────────────────
    #  Utilidades
    # ────────────────────────────────────────────────────────
    @staticmethod
    def _calculate_shipping(subtotal, city=''):
        FREE_SHIPPING_THRESHOLD = Decimal('500000')
        STANDARD_SHIPPING = Decimal('15000')
        return Decimal('0') if subtotal >= FREE_SHIPPING_THRESHOLD else STANDARD_SHIPPING

    @staticmethod
    def get_order_for_user(order_id, user):
        try:
            return Order.objects.prefetch_related('items', 'logs').get(
                id=order_id, user=user
            )
        except Order.DoesNotExist:
            return None
