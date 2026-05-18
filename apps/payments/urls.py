# apps/payments/urls.py
from django.urls import path
from .views import (
    WompiRedirectView, WompiWebhookView,
    PayURedirectView, PayUWebhookView, PayUResponseView,
    MercadoPagoRedirectView, MercadoPagoWebhookView,
)

app_name = 'payments'

urlpatterns = [
    # Wompi
    path('wompi/<int:order_id>/', WompiRedirectView.as_view(), name='wompi_redirect'),
    path('wompi/webhook/', WompiWebhookView.as_view(), name='wompi_webhook'),

    # PayU
    path('payu/<int:order_id>/', PayURedirectView.as_view(), name='payu_redirect'),
    path('payu/webhook/', PayUWebhookView.as_view(), name='payu_webhook'),
    path('payu/respuesta/', PayUResponseView.as_view(), name='payu_response'),

    # MercadoPago
    path('mp/<int:order_id>/', MercadoPagoRedirectView.as_view(), name='mp_redirect'),
    path('mp/webhook/', MercadoPagoWebhookView.as_view(), name='mp_webhook'),
]
