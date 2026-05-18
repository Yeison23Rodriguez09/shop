# apps/payments/services/mercadopago.py
"""
MercadoPago Colombia — integración de pagos.
Documentación: https://www.mercadopago.com.co/developers/es/docs

Flujo:
  1. Backend crea una "preferencia" en la API de MercadoPago
  2. Se obtiene un init_point (URL de pago) o un brick_id para el frontend
  3. Usuario completa el pago en MP
  4. MP envía IPN/webhook a /pagos/mp/webhook/
  5. El webhook llama OrderService.confirm_payment()

Variables de entorno requeridas (.env):
  MP_ACCESS_TOKEN       → token de acceso (TEST-... en sandbox, APP_USR-... en prod)
  MP_PUBLIC_KEY         → clave pública para el frontend SDK
  MP_SANDBOX            → True en desarrollo
"""
import logging
import requests
from django.conf import settings

logger = logging.getLogger('payments.mercadopago')

MP_API_BASE = 'https://api.mercadopago.com'


class MercadoPagoService:

    @staticmethod
    def _headers():
        token = getattr(settings, 'MP_ACCESS_TOKEN', '')
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'X-Idempotency-Key': '',  # se puede sobrescribir por llamada
        }

    # ── Crear preferencia de pago ────────────────────────────

    @staticmethod
    def create_preference(order):
        """
        Crea una preferencia en MercadoPago y retorna el init_point (URL de pago).

        Retorna: dict con 'id', 'init_point', 'sandbox_init_point'
        Lanza: RuntimeError si falla la API
        """
        site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')

        items = []
        for item in order.items.all():
            items.append({
                'id': str(item.product_id),
                'title': item.product_name,
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'currency_id': 'COP',
            })

        payload = {
            'external_reference': order.reference,
            'items': items,
            'payer': {
                'email': order.user.email,
                'name': order.shipping_name,
                'phone': {'number': order.shipping_phone},
            },
            'back_urls': {
                'success': f'{site_url}/pedidos/{order.id}/confirmacion/',
                'failure': f'{site_url}/pedidos/{order.id}/pago-fallido/',
                'pending': f'{site_url}/pedidos/{order.id}/pago-pendiente/',
            },
            'auto_return': 'approved',
            'notification_url': f'{site_url}/pagos/mp/webhook/',
            'statement_descriptor': 'ARES Seguridad',
        }

        try:
            response = requests.post(
                f'{MP_API_BASE}/checkout/preferences',
                json=payload,
                headers=MercadoPagoService._headers(),
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()
            logger.info('MP preferencia creada | id=%s | order=%s', data.get('id'), order.id)
            return data
        except Exception as e:
            logger.error('Error creando preferencia MP para orden %s: %s', order.id, e)
            raise RuntimeError(f'MercadoPago no disponible: {e}')

    # ── Consultar pago ────────────────────────────────────────

    @staticmethod
    def get_payment(payment_id):
        """Consulta los detalles de un pago por su ID."""
        try:
            r = requests.get(
                f'{MP_API_BASE}/v1/payments/{payment_id}',
                headers=MercadoPagoService._headers(),
                timeout=10,
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.error('Error consultando pago MP %s: %s', payment_id, e)
            return None

    # ── Procesar notificación (IPN / webhook) ─────────────────

    @staticmethod
    def process_notification(query_params):
        """
        Procesa la notificación de MercadoPago (IPN o webhook).
        MP envía: ?id=...&topic=payment  o  ?type=payment&data.id=...

        Retorna: (order, success)
        """
        from apps.orders.services.order_service import OrderService

        # Soportar ambos formatos de notificación de MP
        topic = query_params.get('topic') or query_params.get('type')
        payment_id = query_params.get('id') or query_params.get('data.id')

        if topic not in ('payment', 'merchant_order'):
            return None, False

        payment_data = MercadoPagoService.get_payment(payment_id)
        if not payment_data:
            return None, False

        status = payment_data.get('status')
        reference = payment_data.get('external_reference', '')
        gateway_amount_raw = payment_data.get('transaction_amount')
        gateway_currency = payment_data.get('currency_id', 'COP')

        if status != 'approved':
            logger.info('MP notificacion: pago %s con estado %s — ignorando.', payment_id, status)
            return None, False

        gateway_amount = None
        if gateway_amount_raw is not None:
            try:
                from decimal import Decimal
                gateway_amount = Decimal(str(gateway_amount_raw)).quantize(Decimal('0.01'))
            except Exception:
                logger.error('MP: transaction_amount invalido (%r) payment=%s',
                             gateway_amount_raw, payment_id)
                return None, False

        order = OrderService.confirm_payment(
            order_reference=reference,
            payment_id=str(payment_id),
            gateway_name='mercadopago',
            gateway_amount=gateway_amount,
            gateway_currency=gateway_currency,
        )
        return order, order is not None
