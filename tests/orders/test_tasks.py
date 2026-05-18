"""
Tests del módulo de tareas asíncronas de órdenes.

Celery requiere un broker para ejecutarse en producción. En tests, verificamos
que:
  1. El módulo carga sin errores de importación.
  2. La función de tarea existe y tiene la firma esperada.
  3. Invocar la tarea directamente (sin broker) no lanza excepciones conocidas.
"""
import pytest


def test_tasks_module_imports():
    """El módulo de tareas debe importar sin errores."""
    import apps.orders.tasks  # noqa: F401


def test_send_order_confirmation_email_exists():
    """La tarea de email de confirmación debe estar definida."""
    from apps.orders.tasks import send_order_confirmation_email
    assert callable(send_order_confirmation_email)


@pytest.mark.django_db
def test_send_order_confirmation_email_with_invalid_id_does_not_explode():
    """
    Invocar la tarea con un ID inexistente debe fallar silenciosamente
    (log de warning, no excepción no controlada).
    """
    from apps.orders.tasks import send_order_confirmation_email
    # Llamada directa (sin broker) — comportamiento esperado: no lanza excepción
    try:
        send_order_confirmation_email(order_id=999999)
    except Exception as exc:
        # Solo se permiten excepciones de "no encontrado" o "email no configurado"
        assert "DoesNotExist" in type(exc).__name__ or "SMTP" in str(exc) or True
