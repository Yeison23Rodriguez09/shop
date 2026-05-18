# apps/payments/services/wompi.py
"""
Wompi (Bancolombia) — integración de pagos.
Documentación: https://docs.wompi.co/

Flujo:
  1. El usuario selecciona Wompi en el checkout
  2. Se genera un enlace de pago (Widget o Checkout Link)
  3. Wompi redirige al usuario de vuelta con la transacción
  4. Wompi envía un webhook a /pagos/wompi/webhook/
  5. El webhook llama OrderService.confirm_payment()

Variables de entorno requeridas (.env):
  WOMPI_PUBLIC_KEY      → clave pública (pub_...)
  WOMPI_PRIVATE_KEY     → clave privada (prv_...) — solo en servidor
  WOMPI_EVENTS_SECRET   → secreto para validar firma de webhooks
  WOMPI_SANDBOX         → True en desarrollo, False en producción
"""
import hashlib
import hmac
import logging
import requests
from django.conf import settings

logger = logging.getLogger('payments.wompi')

WOMPI_API_BASE = 'https://sandbox.wompi.co/v1' if getattr(settings, 'WOMPI_SANDBOX', True) \
    else 'https://production.wompi.co/v1'
WOMPI_WIDGET_BASE = 'https://checkout.wompi.co/p/'


class WompiService:

    # ── Generación del enlace de pago ────────────────────────

    @staticmethod
    def build_checkout_url(order):
        """
        Construye la URL del widget de pago de Wompi.
        El usuario es redirigido a esta URL para completar el pago.

        Retorna: str URL
        """
        from django.urls import reverse
        import urllib.parse

        public_key = getattr(settings, 'WOMPI_PUBLIC_KEY', '')
        if not public_key:
            raise ValueError('WOMPI_PUBLIC_KEY no está configurada en settings.')

        # Wompi recibe el monto en centavos (COP cents = COP * 100)
        amount_in_cents = int(order.total_price * 100)

        # Firma de integridad: SHA-256(reference + amount + currency + secret)
        integrity_secret = getattr(settings, 'WOMPI_EVENTS_SECRET', '')
        signature_string = f'{order.reference}{amount_in_cents}COP{integrity_secret}'
        integrity = hashlib.sha256(signature_string.encode()).hexdigest()

        redirect_url = getattr(settings, 'SITE_URL', 'http://localhost:8000') + \
            f'/pedidos/{order.id}/confirmacion/'

        params = {
            'public-key': public_key,
            'currency': 'COP',
            'amount-in-cents': amount_in_cents,
            'reference': order.reference,
            'redirect-url': redirect_url,
            'signature:integrity': integrity,
        }

        url = WOMPI_WIDGET_BASE + '?' + urllib.parse.urlencode(params)
        logger.info('Wompi checkout URL generada | order=%s | ref=%s', order.id, order.reference)
        return url

    # ── Validación del webhook ────────────────────────────────

    @staticmethod
    def validate_webhook_signature(payload_bytes, checksum_header):
        """
        Valida que el webhook viene realmente de Wompi.
        Wompi envia el header 'x-event-checksum'.

        En produccion (DEBUG=False), si no hay secret configurado se RECHAZA
        el webhook (fail-closed). En dev se acepta para facilitar pruebas.
        """
        secret = getattr(settings, 'WOMPI_EVENTS_SECRET', '')
        if not secret:
            if not getattr(settings, 'DEBUG', False):
                logger.error('WOMPI_EVENTS_SECRET ausente en produccion — webhook rechazado.')
                return False
            logger.warning('WOMPI_EVENTS_SECRET no configurado — saltando validacion (DEBUG).')
            return True

        expected = hmac.new(
            secret.encode(),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, checksum_header or '')

    # ── Consulta de transacción ───────────────────────────────

    @staticmethod
    def get_transaction(transaction_id):
        """Consulta el estado de una transacción directamente en la API de Wompi."""
        private_key = getattr(settings, 'WOMPI_PRIVATE_KEY', '')
        url = f'{WOMPI_API_BASE}/transactions/{transaction_id}'
        try:
            response = requests.get(
                url,
                headers={'Authorization': f'Bearer {private_key}'},
                timeout=10,
            )
            response.raise_for_status()
            return response.json().get('data', {})
        except Exception as e:
            logger.error('Error consultando transacción Wompi %s: %s', transaction_id, e)
            return None

    # ── Procesamiento del evento webhook ──────────────────────

    @staticmethod
    def process_webhook_event(event_data):
        """
        Procesa el payload JSON de un evento Wompi.
        Retorna: (order, success) o (None, False)
        """
        from apps.orders.services.order_service import OrderService

        event_type = event_data.get('event')
        if event_type != 'transaction.updated':
            return None, False

        tx = event_data.get('data', {}).get('transaction', {})
        status = tx.get('status')
        reference = tx.get('reference')
        tx_id = tx.get('id')
        amount_in_cents = tx.get('amount_in_cents')

        if status != 'APPROVED':
            logger.info('Wompi webhook: transaccion %s con estado %s — ignorando.', tx_id, status)
            return None, False

        # Convertir centavos a Decimal con la misma escala que order.total_price.
        gateway_amount = None
        if amount_in_cents is not None:
            try:
                from decimal import Decimal
                gateway_amount = (Decimal(str(amount_in_cents)) / Decimal('100')).quantize(Decimal('0.01'))
            except Exception:
                logger.error('Wompi: amount_in_cents invalido (%r) tx=%s', amount_in_cents, tx_id)
                return None, False

        order = OrderService.confirm_payment(
            order_reference=reference,
            payment_id=tx_id,
            gateway_name='wompi',
            gateway_amount=gateway_amount,
            gateway_currency=tx.get('currency', 'COP'),
        )
        return order, order is not None
