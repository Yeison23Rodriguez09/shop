# beauty_shop/apps/payments/paypal.py
import requests
from typing import Tuple
from django.conf import settings
from apps.orders.models import Order

PAYPAL_API_BASE = (
    "https://api-m.paypal.com" if getattr(settings, 'PAYPAL_LIVE_MODE', False)
    else "https://api-m.sandbox.paypal.com"
)


def get_access_token() -> str:
    """
    Obtiene el token de acceso OAuth 2.0 desde la API de PayPal.
    """
    auth = (settings.PAYPAL_CLIENT_ID, settings.PAYPAL_SECRET)
    headers = {
        'Accept': 'application/json',
        'Accept-Language': 'en_US',
    }
    data = {'grant_type': 'client_credentials'}

    response = requests.post(
        f"{PAYPAL_API_BASE}/v1/oauth2/token",
        headers=headers,
        data=data,
        auth=auth
    )
    response.raise_for_status()
    return response.json()['access_token']


def create_order(order: Order) -> Tuple[str, str]:
    """
    Crea una orden de PayPal para el modelo Order dado.

    Retorna:
        (order_id, approval_url)
    """
    token = get_access_token()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',
    }

    payload = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "reference_id": str(order.id),
            "amount": {
                "currency_code": "USD",
                "value": f"{order.total_price:.2f}"
            }
        }],
        "application_context": {
            "return_url": f"{settings.DOMAIN_URL}/orders/success/",
            "cancel_url": f"{settings.DOMAIN_URL}/orders/cancel/"
        }
    }

    response = requests.post(
        f"{PAYPAL_API_BASE}/v2/checkout/orders",
        headers=headers,
        json=payload
    )
    response.raise_for_status()
    data = response.json()

    approval_url = next(
        (link["href"] for link in data["links"] if link["rel"] == "approve"),
        None
    )

    if not approval_url:
        raise ValueError("No se pudo obtener la URL de aprobación de PayPal.")

    return data["id"], approval_url


def capture_order(paypal_order_id: str) -> bool:
    """
    Captura el pago de una orden PayPal previamente aprobada.

    Args:
        paypal_order_id (str): ID de la orden de PayPal.

    Returns:
        bool: True si se capturó exitosamente, False en caso contrario.
    """
    token = get_access_token()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',
    }

    response = requests.post(
        f"{PAYPAL_API_BASE}/v2/checkout/orders/{paypal_order_id}/capture",
        headers=headers
    )
    response.raise_for_status()
    data = response.json()

    if data.get("status") == "COMPLETED":
        reference_id = data["purchase_units"][0]["reference_id"]
        try:
            order = Order.objects.get(id=reference_id)
            order.status = "paid"
            order.save()
            return True
        except Order.DoesNotExist:
            return False

    return False
