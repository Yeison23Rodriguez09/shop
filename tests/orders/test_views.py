"""
Tests de OrderService: la capa de negocio más crítica del sistema.

Protege contra regresiones en:
  - Creación atómica con descuento de stock
  - Validación de stock insuficiente
  - Ciclo de vida de estados (pending → paid → cancelled)
  - Restauración idempotente de stock al cancelar
  - Confirmación de pago con validación de monto
  - Idempotencia de webhooks duplicados
  - Cálculo de envío (threshold 500k)
"""
import pytest
from decimal import Decimal

from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory

from apps.cart.models import CartItem
from apps.cart.services import CartService
from apps.orders.models import Order
from apps.orders.services.order_service import OrderService


# ─── Helpers ─────────────────────────────────────────────────────────────────

ADDRESS = {
    "name": "Cliente Test",
    "phone": "+57 300 0000000",
    "address": "Cra 7 # 1-01",
    "city": "Bogotá",
    "department": "Cundinamarca",
    "postal_code": "110111",
}


def _make_cart_for(user, product, qty):
    """Crea un CartService autenticado con `qty` unidades del producto."""
    from apps.cart.models import CartItem
    CartItem.objects.filter(user=user).delete()
    CartItem.objects.create(user=user, product=product, quantity=qty)

    rf = RequestFactory()
    req = rf.get("/")
    req.user = user
    req.session = SessionStore()
    req.session.create()
    return CartService(req)


# ─── Creación de orden ────────────────────────────────────────────────────────

@pytest.mark.django_db(transaction=True)
class TestOrderServiceCreate:

    def test_creates_order_with_correct_total(self, user, product):
        # product.price = 350_000; 1 × 350k < 500k → envío = 15_000
        cart = _make_cart_for(user, product, 1)
        order = OrderService.create_from_cart(cart, user, ADDRESS)
        assert order.subtotal == product.price
        assert order.shipping_cost == Decimal("15000")
        assert order.total_price == product.price + Decimal("15000")

    def test_free_shipping_above_threshold(self, user, sub_category):
        from apps.catalog.models import Product as P
        expensive = P.objects.create(
            name="Producto Caro", slug="prod-caro",
            category=sub_category, price=Decimal("600000"), stock=5,
        )
        cart = _make_cart_for(user, expensive, 1)
        order = OrderService.create_from_cart(cart, user, ADDRESS)
        assert order.shipping_cost == Decimal("0")

    def test_decrements_product_stock(self, user, product):
        stock_before = product.stock
        cart = _make_cart_for(user, product, 3)
        OrderService.create_from_cart(cart, user, ADDRESS)
        product.refresh_from_db()
        assert product.stock == stock_before - 3

    def test_raises_on_empty_cart(self, user, product):
        CartItem.objects.filter(user=user).delete()
        rf = RequestFactory()
        req = rf.get("/")
        req.user = user
        req.session = SessionStore()
        req.session.create()
        empty_cart = CartService(req)
        with pytest.raises(ValueError, match="[Vv]ac|[Ee]mpty"):
            OrderService.create_from_cart(empty_cart, user, ADDRESS)

    def test_raises_on_insufficient_stock(self, user, product):
        product.stock = 2
        product.save()
        cart = _make_cart_for(user, product, 5)
        with pytest.raises(ValueError, match="[Ss]tock"):
            OrderService.create_from_cart(cart, user, ADDRESS)
        product.refresh_from_db()
        assert product.stock == 2  # sin cambios

    def test_order_starts_as_pending(self, user, product):
        cart = _make_cart_for(user, product, 1)
        order = OrderService.create_from_cart(cart, user, ADDRESS)
        assert order.status == "pending"

    def test_order_log_created_on_creation(self, user, product):
        cart = _make_cart_for(user, product, 1)
        order = OrderService.create_from_cart(cart, user, ADDRESS)
        assert order.logs.filter(new_status="pending").exists()


# ─── Ciclo de vida / estados ──────────────────────────────────────────────────

@pytest.mark.django_db(transaction=True)
class TestOrderServiceStatus:

    def _create_order(self, user, product, qty=2):
        cart = _make_cart_for(user, product, qty)
        return OrderService.create_from_cart(cart, user, ADDRESS)

    def test_cancel_restores_stock(self, user, product):
        stock_before = product.stock
        order = self._create_order(user, product, qty=3)
        product.refresh_from_db()
        stock_after_order = product.stock
        assert stock_after_order == stock_before - 3

        OrderService.change_status(order, "cancelled")
        product.refresh_from_db()
        assert product.stock == stock_before

    def test_cancel_twice_does_not_double_restore(self, user, product):
        """Cancelar una orden ya cancelada no debe sumar stock dos veces."""
        stock_before = product.stock
        order = self._create_order(user, product, qty=2)

        OrderService.change_status(order, "cancelled")
        OrderService.change_status(order, "cancelled")  # idempotente

        product.refresh_from_db()
        assert product.stock == stock_before

    def test_refund_restores_stock(self, user, product):
        stock_before = product.stock
        order = self._create_order(user, product, qty=2)
        # Confirmar pago primero
        order.status = "paid"
        order.save()

        OrderService.change_status(order, "refunded")
        product.refresh_from_db()
        assert product.stock == stock_before

    def test_change_status_creates_log(self, user, product):
        order = self._create_order(user, product, qty=1)
        OrderService.change_status(order, "processing", note="En preparación")
        assert order.logs.filter(new_status="processing").exists()

    def test_change_status_same_state_returns_false(self, user, product):
        order = self._create_order(user, product, qty=1)
        result = OrderService.change_status(order, "pending")
        assert result is False


# ─── Confirmación de pago ─────────────────────────────────────────────────────

@pytest.mark.django_db(transaction=True)
class TestOrderServiceConfirmPayment:

    def _create_pending_order(self, user, product):
        cart = _make_cart_for(user, product, 1)
        return OrderService.create_from_cart(cart, user, ADDRESS)

    def test_confirm_payment_sets_paid(self, user, product):
        order = self._create_pending_order(user, product)
        paid = OrderService.confirm_payment(
            order_reference=order.reference,
            payment_id="TX-TEST-OK",
            gateway_name="wompi",
            gateway_amount=order.total_price,
        )
        assert paid is not None
        assert paid.is_paid
        assert paid.payment_id == "TX-TEST-OK"

    def test_confirm_wrong_amount_returns_none(self, user, product):
        order = self._create_pending_order(user, product)
        result = OrderService.confirm_payment(
            order_reference=order.reference,
            payment_id="TX-BAD",
            gateway_name="wompi",
            gateway_amount=Decimal("1.00"),  # monto incorrecto
        )
        assert result is None
        order.refresh_from_db()
        assert order.status == "pending"

    def test_confirm_duplicate_webhook_is_idempotent(self, user, product):
        order = self._create_pending_order(user, product)
        OrderService.confirm_payment(
            order_reference=order.reference,
            payment_id="TX-IDEM",
            gateway_name="wompi",
            gateway_amount=order.total_price,
        )
        # Segunda llamada idéntica
        result = OrderService.confirm_payment(
            order_reference=order.reference,
            payment_id="TX-IDEM",
            gateway_name="wompi",
            gateway_amount=order.total_price,
        )
        assert result is not None
        assert result.status == "paid"
        # Solo un log de transición a paid
        assert result.logs.filter(new_status="paid").count() == 1

    def test_confirm_unknown_reference_returns_none(self, user):
        result = OrderService.confirm_payment(
            order_reference="ARES-NOEXISTE-0000",
            payment_id="TX-X",
            gateway_name="wompi",
            gateway_amount=Decimal("100000"),
        )
        assert result is None

    def test_confirm_without_amount_is_rejected(self, user, product):
        """Sin gateway_amount el pago debe rechazarse (fail-closed)."""
        order = self._create_pending_order(user, product)
        result = OrderService.confirm_payment(
            order_reference=order.reference,
            payment_id="TX-NO-AMT",
            gateway_name="wompi",
            gateway_amount=None,
        )
        assert result is None, "Pago sin monto NO debe confirmarse (fail-closed)"
        order.refresh_from_db()
        assert order.status == "pending", "La orden debe seguir pending"
        assert not order.is_paid
