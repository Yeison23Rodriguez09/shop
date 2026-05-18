# beauty_shop/apps/payments/stripe.py
import stripe
from django.conf import settings
from apps.orders.models import Order

# La clave se asigna de forma lazy para no fallar cuando la variable no está
# definida (entornos de test, desarrollo sin Stripe configurado).
stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')


def create_checkout_session(order: Order) -> str:
    """
    Crea una sesión de pago en Stripe para una orden específica.

    Args:
        order (Order): Instancia del modelo Order.

    Returns:
        str: ID de la sesión de checkout, para redirigir al frontend.
    """
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f"Pedido #{order.id}",
                        },
                        'unit_amount': int(order.total_price * 100),  # Stripe trabaja en centavos
                    },
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=f"{settings.DOMAIN_URL}/orders/success/",
            cancel_url=f"{settings.DOMAIN_URL}/orders/cancel/",
            metadata={'order_id': str(order.id)},
        )
        return session.id
    except stripe.error.StripeError as e:
        # Aquí puedes loguear o lanzar un error personalizado
        raise RuntimeError(f"Error al crear la sesión de Stripe: {str(e)}")


def handle_checkout_session_completed(session_data: dict) -> bool:
    """
    Procesa el webhook de Stripe cuando una sesión de checkout es completada.

    Args:
        session_data (dict): Datos recibidos del webhook de Stripe.

    Returns:
        bool: True si la orden fue encontrada y actualizada correctamente.
    """
    order_id = session_data.get('metadata', {}).get('order_id')
    if not order_id:
        return False

    try:
        order = Order.objects.get(pk=order_id)
        order.status = 'paid'
        order.save()
        return True
    except Order.DoesNotExist:
        return False
