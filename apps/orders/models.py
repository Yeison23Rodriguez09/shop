# apps/orders/models.py
import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from apps.catalog.models import Product, ProductVariant


# ═══════════════════════════════════════════════════════════
#  Orden de compra
# ═══════════════════════════════════════════════════════════
class Order(models.Model):

    STATUS_CHOICES = [
        ('pending',   'Pendiente de pago'),
        ('paid',      'Pagado'),
        ('processing','En preparación'),
        ('shipped',   'Enviado'),
        ('delivered', 'Entregado'),
        ('cancelled', 'Cancelado'),
        ('refunded',  'Reembolsado'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('wompi',        'Wompi (Bancolombia)'),
        ('payu',         'PayU'),
        ('mercadopago',  'MercadoPago'),
        ('transfer',     'Transferencia bancaria'),
        ('cash',         'Pago en efectivo (contraentrega)'),
    ]

    # ── Identificación ──────────────────────────────────────
    reference = models.CharField(
        'Referencia única', max_length=32, unique=True, blank=True,
        help_text='Generada automáticamente. Se usa en pasarelas de pago.',
    )

    # ── Relaciones ──────────────────────────────────────────
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='Cliente',
    )

    # ── Estado y pago ───────────────────────────────────────
    status = models.CharField(
        'Estado', max_length=20,
        choices=STATUS_CHOICES, default='pending',
    )
    payment_method = models.CharField(
        'Método de pago', max_length=20,
        choices=PAYMENT_METHOD_CHOICES, blank=True,
    )
    payment_id = models.CharField(
        'ID de transacción (pasarela)', max_length=200, blank=True,
        help_text='ID devuelto por la pasarela de pago.',
    )
    paid_at = models.DateTimeField('Fecha de pago', null=True, blank=True)

    # ── Totales ─────────────────────────────────────────────
    subtotal = models.DecimalField('Subtotal', max_digits=12, decimal_places=2, default=0)
    shipping_cost = models.DecimalField('Costo de envío', max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField('Total', max_digits=12, decimal_places=2, default=0)

    # ── Dirección de entrega (snapshot al momento de compra) ─
    shipping_name = models.CharField('Nombre destinatario', max_length=200, blank=True)
    shipping_phone = models.CharField('Teléfono', max_length=30, blank=True)
    shipping_address = models.CharField('Dirección', max_length=255, blank=True)
    shipping_city = models.CharField('Ciudad', max_length=100, blank=True)
    shipping_department = models.CharField('Departamento', max_length=100, blank=True)
    shipping_postal_code = models.CharField('Código postal', max_length=10, blank=True)
    shipping_notes = models.TextField('Instrucciones de entrega', blank=True)

    # ── Notas internas ──────────────────────────────────────
    internal_notes = models.TextField('Notas internas', blank=True)

    # ── Timestamps ──────────────────────────────────────────
    created_at = models.DateTimeField('Creado el', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado el', auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Orden'
        verbose_name_plural = 'Órdenes'

    def __str__(self):
        return f'Pedido #{self.id} — {self.user.email} [{self.get_status_display()}]'

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self._generate_reference()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_reference():
        """Referencia tipo ARES-20240101-XXXX para mostrar al cliente y enviar a pasarelas."""
        from django.utils import timezone
        date_str = timezone.now().strftime('%Y%m%d')
        uid = uuid.uuid4().hex[:6].upper()
        return f'ARES-{date_str}-{uid}'

    def calculate_total(self):
        """Recalcula subtotal y total desde los ítems."""
        self.subtotal = sum(item.subtotal for item in self.items.all())
        self.total_price = self.subtotal + self.shipping_cost
        self.save(update_fields=['subtotal', 'total_price'])
        return self.total_price

    @property
    def is_paid(self):
        return self.status in ('paid', 'processing', 'shipped', 'delivered')

    @property
    def status_color(self):
        colors = {
            'pending':    '#c8a45a',   # dorado Ares
            'paid':       '#27ae60',   # verde
            'processing': '#2980b9',   # azul
            'shipped':    '#8e44ad',   # morado
            'delivered':  '#27ae60',   # verde
            'cancelled':  '#e74c3c',   # rojo
            'refunded':   '#95a5a6',   # gris
        }
        return colors.get(self.status, '#aaa')


# ═══════════════════════════════════════════════════════════
#  Ítem de la orden
# ═══════════════════════════════════════════════════════════
class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE,
        related_name='items', verbose_name='Orden',
    )
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT,
        verbose_name='Producto',
    )
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.PROTECT,
        null=True, blank=True,
        verbose_name='Variante',
    )
    # Snapshot del producto al momento de la compra
    product_name = models.CharField('Nombre del producto', max_length=200)
    product_model = models.CharField('Modelo', max_length=100, blank=True)
    variant_color = models.CharField('Color comprado', max_length=60, blank=True)
    variant_sku = models.CharField('SKU comprado', max_length=80, blank=True)
    quantity = models.PositiveIntegerField('Cantidad', default=1)
    unit_price = models.DecimalField('Precio unitario', max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = 'Ítem de orden'
        verbose_name_plural = 'Ítems de orden'

    def __str__(self):
        return f'{self.quantity} × {self.product_name}'

    @property
    def subtotal(self):
        return self.unit_price * self.quantity


# ═══════════════════════════════════════════════════════════
#  Log de cambios de estado — auditoría completa
# ═══════════════════════════════════════════════════════════
class OrderLog(models.Model):
    """
    Registro inmutable de cada cambio de estado de una orden.
    Nunca se elimina. Es la historia completa del pedido.
    """
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE,
        related_name='logs', verbose_name='Orden',
    )
    previous_status = models.CharField('Estado anterior', max_length=20, blank=True)
    new_status = models.CharField('Nuevo estado', max_length=20)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='order_logs',
        verbose_name='Cambiado por',
    )
    note = models.TextField('Nota', blank=True,
                            help_text='Razón del cambio, mensaje al cliente, etc.')
    source = models.CharField(
        'Origen', max_length=30, default='system',
        help_text='system / admin / webhook_wompi / webhook_payu / webhook_mp',
    )
    created_at = models.DateTimeField('Registrado el', auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Log de orden'
        verbose_name_plural = 'Logs de órdenes'

    def __str__(self):
        return (f'Orden #{self.order_id}: '
                f'{self.previous_status or "—"} → {self.new_status} '
                f'({self.created_at:%d/%m/%Y %H:%M})')
