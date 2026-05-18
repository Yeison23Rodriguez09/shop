"""
Tests de modelos de pedidos: Order, OrderItem.

Verifica que los modelos cumplen sus invariantes de dominio sin depender
de servicios externos ni lógica de vistas.
"""
import pytest
from decimal import Decimal

from apps.orders.models import Order, OrderItem


@pytest.mark.django_db
class TestOrderModel:

    def _create_order(self, user):
        return Order.objects.create(
            user=user,
            status="pending",
            payment_method="wompi",
            subtotal=Decimal("300000"),
            shipping_cost=Decimal("15000"),
            total_price=Decimal("315000"),
            shipping_name="Test Cliente",
            shipping_address="Calle 1 # 2-3",
            shipping_city="Bogotá",
        )

    def test_reference_auto_generated_on_save(self, user):
        order = self._create_order(user)
        assert order.reference
        assert len(order.reference) > 6

    def test_reference_unique_per_order(self, user):
        o1 = self._create_order(user)
        o2 = self._create_order(user)
        assert o1.reference != o2.reference

    def test_reference_contains_ares_prefix(self, user):
        order = self._create_order(user)
        assert order.reference.startswith("ARES-")

    def test_is_paid_false_when_pending(self, user):
        order = self._create_order(user)
        assert order.is_paid is False

    def test_is_paid_true_when_status_paid(self, user):
        order = self._create_order(user)
        order.status = "paid"
        order.save()
        assert order.is_paid is True

    def test_str_contains_user_email(self, user):
        order = self._create_order(user)
        assert user.email in str(order)

    def test_status_choices_include_all_states(self, user):
        order = self._create_order(user)
        valid_statuses = {s[0] for s in Order.STATUS_CHOICES}
        for status in ("pending", "paid", "processing", "shipped",
                       "delivered", "cancelled", "refunded"):
            assert status in valid_statuses
