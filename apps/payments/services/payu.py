# apps/payments/services/payu.py
"""
PayU Colombia — integración de pagos.
Documentación: https://developers.payulatam.com/latam/es/docs/

Flujo:
  1. Usuario selecciona PayU → se genera un formulario POST hacia PayU
  2. PayU procesa el pago y redirige al usuario de vuelta (response/confirmation URLs)
  3. PayU envía una notificación asíncrona (IPN) a /pagos/payu/webhook/
  4. El webhook llama OrderService.confirm_payment()

Variables de entorno requeridas (.env):
  PAYU_API_KEY          → clave API de PayU
  PAYU_MERCHANT_ID      → ID del comercio
  PAYU_ACCOUNT_ID       → ID de la cuenta (Colombia = 512321 en sandbox)
  PAYU_SANDBOX          → True en desarrollo
"""
import hashlib
import logging
from django.conf import settings

logger = logging.getLogger('payments.payu')

PAYU_SANDBOX_URL = 'https://sandbox.checkout.payulatam.com/ppp-web-gateway-payu/'
PAYU_PROD_URL = 'https://checkout.payulatam.com/ppp-web-gateway-payu/'


class PayUService:

    # ── Generación del formulario ────────────────────────────

    @staticmethod
    def build_payment_form_data(order):
        """
        Genera los campos del formulario POST que envía al checkout de PayU.
        Se usa en el template con un <form method='POST' action='...'>

        Retorna: dict con todos los campos y la URL de acción.
        """
        api_key = getattr(settings, 'PAYU_API_KEY', '')
        merchant_id = getattr(settings, 'PAYU_MERCHANT_ID', '')
        account_id = getattr(settings, 'PAYU_ACCOUNT_ID', '')
        sandbox = getattr(settings, 'PAYU_SANDBOX', True)

        if not all([api_key, merchant_id, account_id]):
            raise ValueError('Configuración de PayU incompleta en settings.')

        site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')

        # Firma MD5: apiKey~merchantId~referenceCode~amount~currency
        amount = f'{order.total_price:.2f}'
        currency = 'COP'
        signature_str = f'{api_key}~{merchant_id}~{order.reference}~{amount}~{currency}'
        signature = hashlib.md5(signature_str.encode()).hexdigest()

        form_data = {
            'merchantId': merchant_id,
            'accountId': account_id,
            'description': f'Pedido Nexo YR Secure #{order.id} — Seguridad Electrónica',
            'referenceCode': order.reference,
            'amount': amount,
            'currency': currency,
            'signature': signature,
            'tax': '0',
            'taxReturnBase': '0',
            'buyerEmail': order.user.email,
            'buyerFullName': order.shipping_name or order.user.email,
            'buyerPhone': order.shipping_phone or '',
            'shippingAddress': order.shipping_address,
            'shippingCity': order.shipping_city,
            'shippingCountry': 'CO',
            'responseUrl': f'{site_url}/pagos/payu/respuesta/',
            'confirmationUrl': f'{site_url}/pagos/payu/webhook/',
            'test': '1' if sandbox else '0',
        }

        action_url = PAYU_SANDBOX_URL if sandbox else PAYU_PROD_URL

        logger.info('PayU form data generado | order=%s | ref=%s', order.id, order.reference)
        return {'fields': form_data, 'action_url': action_url}

    # ── Validación del IPN ────────────────────────────────────

    @staticmethod
    def validate_ipn_signature(post_data):
        """
        Valida la firma de la notificación IPN de PayU.
        PayU envía: sign = MD5(apiKey~merchantId~referenceCode~TX_VALUE~currency~transactionState)
        """
        api_key = getattr(settings, 'PAYU_API_KEY', '')
        merchant_id = getattr(settings, 'PAYU_MERCHANT_ID', '')

        reference = post_data.get('referenceCode', '')
        amount = post_data.get('TX_VALUE', '')
        currency = post_data.get('currency', '')
        state = post_data.get('transactionState', '')
        received_sign = post_data.get('sign', '')

        sig_str = f'{api_key}~{merchant_id}~{reference}~{amount}~{currency}~{state}'
        expected = hashlib.md5(sig_str.encode()).hexdigest()
        return expected == received_sign

    # ── Procesamiento del IPN ──────────────────────────────────

    @staticmethod
    def process_ipn(post_data):
        """
        Procesa la notificación de pago de PayU.
        transactionState=4 → APROBADO
        Retorna: (order, success)
        """
        from apps.orders.services.order_service import OrderService

        if not PayUService.validate_ipn_signature(post_data):
            logger.warning('PayU IPN: firma inválida.')
            return None, False

        state = post_data.get('transactionState')
        if state != '4':  # 4 = APPROVED
            logger.info('PayU IPN: estado %s — no aprobado.', state)
            return None, False

        reference = post_data.get('referenceCode', '')
        tx_id = post_data.get('transactionId', '')
        tx_value = post_data.get('TX_VALUE', '')

        gateway_amount = None
        if tx_value:
            try:
                from decimal import Decimal
                gateway_amount = Decimal(tx_value).quantize(Decimal('0.01'))
            except Exception:
                logger.error('PayU: TX_VALUE invalido (%r)', tx_value)
                return None, False

        order = OrderService.confirm_payment(
            order_reference=reference,
            payment_id=tx_id,
            gateway_name='payu',
            gateway_amount=gateway_amount,
            gateway_currency=post_data.get('currency', 'COP'),
        )
        return order, order is not None
