# apps/payments/views.py
import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin

from apps.orders.models import Order

logger = logging.getLogger('payments')


# ═══════════════════════════════════════════════════════════
#  WOMPI
# ═══════════════════════════════════════════════════════════
class WompiRedirectView(LoginRequiredMixin, View):
    """Genera la URL de Wompi y redirige al usuario."""
    login_url = '/accounts/login/'

    def get(self, request, order_id):
        order = get_object_or_404(Order, pk=order_id, user=request.user)
        try:
            from apps.payments.services.wompi import WompiService
            checkout_url = WompiService.build_checkout_url(order)
            return redirect(checkout_url)
        except Exception as e:
            logger.error('Wompi redirect error orden %s: %s', order_id, e)
            from django.contrib import messages
            messages.error(request, 'No se pudo conectar con Wompi. Intenta de nuevo.')
            return redirect('orders:order_detail', pk=order_id)


@method_decorator(csrf_exempt, name='dispatch')
class WompiWebhookView(View):
    """Recibe eventos de Wompi y confirma pagos."""

    def post(self, request):
        from apps.payments.services.wompi import WompiService
        checksum = request.META.get('HTTP_X_EVENT_CHECKSUM', '')

        if not WompiService.validate_webhook_signature(request.body, checksum):
            logger.warning('Wompi webhook: firma inválida.')
            return HttpResponse(status=401)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponse(status=400)

        order, success = WompiService.process_webhook_event(data)
        if success:
            logger.info('Wompi webhook: pago confirmado para orden %s', order.reference)
        return HttpResponse(status=200)


# ═══════════════════════════════════════════════════════════
#  PayU
# ═══════════════════════════════════════════════════════════
class PayURedirectView(LoginRequiredMixin, View):
    """Muestra el formulario POST de PayU para que el usuario confirme y sea redirigido."""
    login_url = '/accounts/login/'

    def get(self, request, order_id):
        order = get_object_or_404(Order, pk=order_id, user=request.user)
        try:
            from apps.payments.services.payu import PayUService
            form_data = PayUService.build_payment_form_data(order)
            return render(request, 'payments/payu_redirect.html', {
                'order': order,
                'payu_fields': form_data['fields'],
                'action_url': form_data['action_url'],
            })
        except Exception as e:
            logger.error('PayU redirect error orden %s: %s', order_id, e)
            from django.contrib import messages
            messages.error(request, 'No se pudo conectar con PayU. Intenta de nuevo.')
            return redirect('orders:order_detail', pk=order_id)


@method_decorator(csrf_exempt, name='dispatch')
class PayUWebhookView(View):
    """Recibe notificación IPN de PayU."""

    def post(self, request):
        from apps.payments.services.payu import PayUService
        order, success = PayUService.process_ipn(request.POST)
        if success:
            logger.info('PayU IPN: pago confirmado para orden %s', order.reference)
        return HttpResponse(status=200)


class PayUResponseView(View):
    """URL de retorno de PayU (el usuario vuelve aquí después de pagar)."""

    def get(self, request):
        tx_state = request.GET.get('transactionState')
        reference = request.GET.get('referenceCode', '')
        if tx_state == '4':  # APROBADO
            try:
                order = Order.objects.get(reference=reference, user=request.user)
                return redirect('orders:order_confirmation', pk=order.pk)
            except Order.DoesNotExist:
                pass
        return redirect('orders:order_list')


# ═══════════════════════════════════════════════════════════
#  MercadoPago
# ═══════════════════════════════════════════════════════════
class MercadoPagoRedirectView(LoginRequiredMixin, View):
    """Crea la preferencia en MP y redirige al checkout."""
    login_url = '/accounts/login/'

    def get(self, request, order_id):
        order = get_object_or_404(Order, pk=order_id, user=request.user)
        try:
            from apps.payments.services.mercadopago import MercadoPagoService
            preference = MercadoPagoService.create_preference(order)
            from django.conf import settings
            sandbox = getattr(settings, 'MP_SANDBOX', True)
            checkout_url = preference.get('sandbox_init_point' if sandbox else 'init_point', '')
            return redirect(checkout_url)
        except Exception as e:
            logger.error('MP redirect error orden %s: %s', order_id, e)
            from django.contrib import messages
            messages.error(request, 'No se pudo conectar con MercadoPago. Intenta de nuevo.')
            return redirect('orders:order_detail', pk=order_id)


@method_decorator(csrf_exempt, name='dispatch')
class MercadoPagoWebhookView(View):
    """Recibe notificaciones IPN/webhook de MercadoPago."""

    def get(self, request):
        """MP también envía GET para IPN."""
        return self._handle(request)

    def post(self, request):
        return self._handle(request)

    def _handle(self, request):
        from apps.payments.services.mercadopago import MercadoPagoService
        order, success = MercadoPagoService.process_notification(request.GET)
        if success:
            logger.info('MP webhook: pago confirmado para orden %s', order.reference)
        return HttpResponse(status=200)
