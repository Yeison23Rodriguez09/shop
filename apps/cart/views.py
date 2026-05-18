from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from apps.catalog.models import Product, ProductVariant
from .services import CartService


class CartDetailView(View):
    def get(self, request):
        cart = CartService(request)
        return render(request, 'cart/cart_detail.html', {
            'cart_items': cart.get_items(),
            'total_price': cart.get_total_price(),
        })


class AddToCartView(View):
    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        try:
            quantity = int(request.POST.get('quantity', 1))
        except (TypeError, ValueError):
            quantity = 1

        # Variante opcional (si el producto tiene variantes activas).
        variant = None
        variant_id = request.POST.get('variant_id') or ''
        if variant_id.strip():
            variant = get_object_or_404(ProductVariant, id=int(variant_id), product=product)

        cart = CartService(request)
        try:
            cart.add(product, quantity, variant=variant)
        except ValueError as e:
            messages.error(request, str(e))
            next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
            return redirect(next_url or 'cart:cart_detail')
        label = product.name + (f' ({variant.color})' if variant else '')
        messages.success(request, f"'{label}' fue agregado al carrito.")

        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
        if next_url:
            return redirect(next_url)
        return redirect('cart:cart_detail')


class UpdateCartView(View):
    """Actualiza la cantidad de un producto (llamado por onchange en el input)."""
    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        try:
            quantity = int(request.POST.get('quantity', 1))
        except (TypeError, ValueError):
            quantity = 1

        cart = CartService(request)
        if quantity < 1:
            cart.remove(product)
        else:
            try:
                cart.update_quantity(product, quantity)
            except ValueError as e:
                messages.error(request, str(e))
        return redirect('cart:cart_detail')


class RemoveFromCartView(View):
    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        cart = CartService(request)
        cart.remove(product)
        messages.info(request, f"'{product.name}' fue eliminado del carrito.")
        return redirect('cart:cart_detail')


class ClearCartView(View):
    def post(self, request):
        cart = CartService(request)
        cart.clear()
        messages.warning(request, "Tu carrito ha sido vaciado.")
        return redirect('cart:cart_detail')
