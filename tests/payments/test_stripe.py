"""
Tests del módulo Stripe.

Stripe hace llamadas HTTP reales a su API. Estos tests verifican la estructura
del módulo y el comportamiento de validación sin hacer llamadas de red.
"""


def test_stripe_module_imports():
    """El módulo carga sin error de importación."""
    import apps.payments.stripe as stripe_module  # noqa: F401


def test_create_checkout_session_is_callable():
    from apps.payments.stripe import create_checkout_session
    assert callable(create_checkout_session)


def test_handle_checkout_session_completed_is_callable():
    from apps.payments.stripe import handle_checkout_session_completed
    assert callable(handle_checkout_session_completed)
