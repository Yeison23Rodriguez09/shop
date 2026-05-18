"""
Señales del carrito.

Cuando un usuario hace login (via allauth o Django nativo),
fusionamos el carrito anónimo de sesión con el carrito en BD.
"""
from django.dispatch import receiver
from allauth.account.signals import user_logged_in


@receiver(user_logged_in)
def merge_cart_on_login(sender, request, user, **kwargs):
    """Fusiona el carrito de sesión anónima en el carrito del usuario recién autenticado."""
    try:
        from apps.cart.services import CartService
        cart = CartService(request)
        cart.merge_session_into_db()
    except Exception:
        pass  # No detener el login por un error de carrito
