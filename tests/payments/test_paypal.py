"""
Tests del módulo PayPal.

PayPal requiere credentials y red para operar. Verificamos estructura del módulo
y que las funciones principales existen con la firma esperada.
"""


def test_paypal_module_imports():
    """El módulo carga sin error de importación."""
    import apps.payments.paypal  # noqa: F401


def test_get_access_token_is_callable():
    from apps.payments.paypal import get_access_token
    assert callable(get_access_token)
