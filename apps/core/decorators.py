# beauty_shop\apps\core\decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def user_is_customer(function):
    """
    Solo permite el acceso si el usuario tiene rol de cliente.
    Requiere que el modelo de usuario tenga un atributo `role`.
    """
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and getattr(request.user, 'role', None) == 'customer':
            return function(request, *args, **kwargs)
        messages.warning(request, "Acceso restringido a clientes.")
        return redirect('core:home')
    return wrap


def anonymous_required(redirect_url='core:home'):
    """
    Evita que usuarios autenticados accedan a ciertas vistas (como login o registro).
    """
    def decorator(function):
        @wraps(function)
        def wrap(request, *args, **kwargs):
            if request.user.is_authenticated:
                return redirect(redirect_url)
            return function(request, *args, **kwargs)
        return wrap
    return decorator


def require_cart_items(function):
    """
    Decorador para asegurar que el carrito no esté vacío antes de continuar (por ejemplo, al pagar).
    """
    @wraps(function)
    def wrap(request, *args, **kwargs):
        cart = request.session.get('cart', {})
        if not cart:
            messages.warning(request, "Tu carrito está vacío.")
            return redirect('cart:cart_detail')
        return function(request, *args, **kwargs)
    return wrap
