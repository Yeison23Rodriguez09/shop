# apps/orders/urls.py
from django.urls import path
from .views import (
    OrderListView,
    OrderDetailView,
    CheckoutAddressView,
    CheckoutPaymentView,
    OrderConfirmationView,
)

app_name = 'orders'

urlpatterns = [
    # Mis pedidos
    path('', OrderListView.as_view(), name='order_list'),
    path('<int:pk>/', OrderDetailView.as_view(), name='order_detail'),
    path('<int:pk>/confirmacion/', OrderConfirmationView.as_view(), name='order_confirmation'),

    # Checkout (flujo)
    path('checkout/direccion/', CheckoutAddressView.as_view(), name='checkout_address'),
    path('checkout/pago/', CheckoutPaymentView.as_view(), name='checkout_payment'),
]
