# apps/orders/views.py
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

from apps.cart.services import CartService
from apps.orders.models import Order
from apps.orders.forms import CheckoutAddressForm, CheckoutPaymentForm
from apps.orders.services.order_service import OrderService

logger = logging.getLogger('orders')


# ═══════════════════════════════════════════════════════════
#  Lista de pedidos del usuario
# ═══════════════════════════════════════════════════════════
class OrderListView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def get(self, request):
        orders = (Order.objects
                  .filter(user=request.user)
                  .prefetch_related('items')
                  .order_by('-created_at'))
        return render(request, 'orders/order_list.html', {'orders': orders})


# ═══════════════════════════════════════════════════════════
#  Detalle de un pedido
# ═══════════════════════════════════════════════════════════
class OrderDetailView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def get(self, request, pk):
        order = get_object_or_404(
            Order.objects.prefetch_related('items', 'logs'),
            pk=pk, user=request.user,
        )
        return render(request, 'orders/order_detail.html', {'order': order})


# ═══════════════════════════════════════════════════════════
#  Checkout — Paso 1: Dirección de entrega
# ═══════════════════════════════════════════════════════════
class CheckoutAddressView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def get(self, request):
        cart = CartService(request)
        if not cart.get_items():
            messages.error(request, 'Tu carrito está vacío.')
            return redirect('catalog:product_list')

        # Pre-llenar con datos del perfil si existen
        initial = {}
        try:
            profile = request.user.profile
            initial = {
                'name': request.user.full_name,
                'phone': profile.phone,
                'address': profile.address_line1,
                'city': profile.city,
                'department': profile.department,
                'postal_code': profile.postal_code,
            }
        except Exception:
            pass

        form = CheckoutAddressForm(initial=initial)
        return render(request, 'orders/checkout_address.html', {
            'form': form,
            'cart': cart,
            'cart_items': cart.get_items(),
            'total_price': cart.get_total_price(),
        })

    def post(self, request):
        cart = CartService(request)
        if not cart.get_items():
            return redirect('catalog:product_list')

        form = CheckoutAddressForm(request.POST)
        if not form.is_valid():
            return render(request, 'orders/checkout_address.html', {
                'form': form,
                'cart': cart,
                'cart_items': cart.get_items(),
                'total_price': cart.get_total_price(),
            })

        # Guardar dirección en sesión para el siguiente paso
        request.session['checkout_address'] = form.cleaned_data

        # Guardar en perfil si el usuario lo pidió
        if form.cleaned_data.get('save_address'):
            try:
                profile = request.user.profile
                profile.phone = form.cleaned_data.get('phone', '')
                profile.address_line1 = form.cleaned_data.get('address', '')
                profile.city = form.cleaned_data.get('city', '')
                profile.department = form.cleaned_data.get('department', '')
                profile.postal_code = form.cleaned_data.get('postal_code', '')
                profile.save()
            except Exception:
                pass

        return redirect('orders:checkout_payment')


# ═══════════════════════════════════════════════════════════
#  Checkout — Paso 2: Método de pago + resumen
# ═══════════════════════════════════════════════════════════
class CheckoutPaymentView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def get(self, request):
        address = request.session.get('checkout_address')
        if not address:
            return redirect('orders:checkout_address')

        cart = CartService(request)
        if not cart.get_items():
            return redirect('catalog:product_list')

        form = CheckoutPaymentForm()
        from decimal import Decimal
        subtotal = cart.get_total_price()
        shipping = Decimal('0') if subtotal >= Decimal('500000') else Decimal('15000')
        return render(request, 'orders/checkout_payment.html', {
            'form': form,
            'address': address,
            'cart_items': cart.get_items(),
            'subtotal': subtotal,
            'shipping': shipping,
            'total': subtotal + shipping,
        })

    def post(self, request):
        address = request.session.get('checkout_address')
        if not address:
            return redirect('orders:checkout_address')

        cart = CartService(request)
        form = CheckoutPaymentForm(request.POST)

        if not form.is_valid():
            return redirect('orders:checkout_payment')

        payment_method = form.cleaned_data['payment_method']

        try:
            order = OrderService.create_from_cart(
                cart_service=cart,
                user=request.user,
                address_data=address,
                payment_method=payment_method,
            )
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('cart:cart_detail')

        # Limpiar carrito y sesión de checkout
        cart.clear()
        request.session.pop('checkout_address', None)

        # Redirigir según la pasarela elegida
        request.session['pending_order_id'] = order.id

        if payment_method == 'wompi':
            return redirect('payments:wompi_redirect', order_id=order.id)
        elif payment_method == 'payu':
            return redirect('payments:payu_redirect', order_id=order.id)
        elif payment_method == 'mercadopago':
            return redirect('payments:mp_redirect', order_id=order.id)
        elif payment_method == 'transfer':
            messages.success(
                request,
                'Tu pedido fue creado. A continuación encontrarás los datos para realizar la transferencia.'
            )
            return redirect('orders:order_confirmation', pk=order.pk)
        elif payment_method == 'cash':
            messages.success(
                request,
                'Tu pedido fue creado. Pagarás contraentrega al momento de recibir el envío.'
            )
            return redirect('orders:order_confirmation', pk=order.pk)
        else:
            messages.info(request, 'Tu pedido fue creado. Recibirás instrucciones por correo.')
            return redirect('orders:order_detail', pk=order.pk)


# ═══════════════════════════════════════════════════════════
#  Confirmación de pago exitoso
# ═══════════════════════════════════════════════════════════
class OrderConfirmationView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk, user=request.user)
        return render(request, 'orders/order_confirmation.html', {'order': order})
