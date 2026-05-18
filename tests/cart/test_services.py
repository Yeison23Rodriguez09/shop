"""
Tests unitarios de CartService.

Cubre ambas rutas de persistencia:
  - Anónimo → sesión (mock request con SessionStore)
  - Autenticado → CartItem en BD

Reglas de negocio verificadas:
  - Acumulación de cantidades
  - Límite de stock (boundary exacto)
  - override_quantity para updates
  - Validación de producto/variante inactivos
  - Fusión de sesión al autenticarse (merge_session_into_db)
  - Precio efectivo: variante > producto base
"""
import pytest
from decimal import Decimal

from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory

from apps.cart.services import CartService
from apps.catalog.models import ProductVariant


# ─── Fixtures de request ─────────────────────────────────────────────────────

def _make_anon_request():
    """Request simulado sin usuario autenticado."""
    from django.contrib.auth.models import AnonymousUser
    rf = RequestFactory()
    req = rf.get("/")
    req.user = AnonymousUser()
    req.session = SessionStore()
    req.session.create()
    return req


def _make_auth_request(user):
    """Request simulado con usuario autenticado."""
    rf = RequestFactory()
    req = rf.get("/")
    req.user = user
    req.session = SessionStore()
    req.session.create()
    return req


# ─── Carrito anónimo (sesión) ─────────────────────────────────────────────────

@pytest.mark.django_db
class TestCartServiceAnonymous:

    def test_add_single_item(self, product):
        cart = CartService(_make_anon_request())
        cart.add(product, quantity=2)
        assert cart.get_item_count() == 2

    def test_add_accumulates(self, product):
        cart = CartService(_make_anon_request())
        cart.add(product, quantity=1)
        cart.add(product, quantity=3)
        assert cart.get_item_count() == 4

    def test_add_at_stock_limit_is_allowed(self, product):
        """Exactamente el stock disponible debe ser aceptado."""
        cart = CartService(_make_anon_request())
        cart.add(product, quantity=product.stock)
        assert cart.get_item_count() == product.stock

    def test_add_exceeds_stock_raises(self, product):
        cart = CartService(_make_anon_request())
        with pytest.raises(ValueError, match="[Ss]tock"):
            cart.add(product, quantity=product.stock + 1)

    def test_add_accumulation_exceeds_stock_raises(self, product):
        cart = CartService(_make_anon_request())
        cart.add(product, quantity=product.stock - 1)
        with pytest.raises(ValueError, match="[Ss]tock"):
            cart.add(product, quantity=2)   # 1 más de lo que queda

    def test_add_zero_quantity_raises(self, product):
        cart = CartService(_make_anon_request())
        with pytest.raises(ValueError):
            cart.add(product, quantity=0)

    def test_add_inactive_product_raises(self, product):
        product.is_active = False
        product.save()
        cart = CartService(_make_anon_request())
        with pytest.raises(ValueError):
            cart.add(product, quantity=1)

    def test_update_quantity(self, product):
        cart = CartService(_make_anon_request())
        cart.add(product, quantity=3)
        cart.update_quantity(product, quantity=5)
        assert cart.get_item_count() == 5

    def test_update_quantity_zero_removes_item(self, product):
        cart = CartService(_make_anon_request())
        cart.add(product, quantity=2)
        cart.update_quantity(product, quantity=0)
        assert cart.get_item_count() == 0

    def test_remove_item(self, product):
        cart = CartService(_make_anon_request())
        cart.add(product, quantity=3)
        cart.remove(product)
        assert cart.get_item_count() == 0

    def test_total_price(self, product):
        cart = CartService(_make_anon_request())
        cart.add(product, quantity=2)
        expected = product.price * 2
        assert cart.get_total_price() == expected

    def test_clear_empties_cart(self, product):
        cart = CartService(_make_anon_request())
        cart.add(product, quantity=3)
        cart.clear()
        assert cart.get_item_count() == 0


# ─── Carrito autenticado (BD) ─────────────────────────────────────────────────

@pytest.mark.django_db
class TestCartServiceAuthenticated:

    def test_add_persists_to_db(self, product, user):
        from apps.cart.models import CartItem
        cart = CartService(_make_auth_request(user))
        cart.add(product, quantity=3)
        item = CartItem.objects.get(user=user, product=product)
        assert item.quantity == 3

    def test_add_accumulates_in_db(self, product, user):
        from apps.cart.models import CartItem
        cart = CartService(_make_auth_request(user))
        cart.add(product, quantity=2)
        cart.add(product, quantity=4)
        item = CartItem.objects.get(user=user, product=product)
        assert item.quantity == 6

    def test_exceeds_stock_raises_db(self, product, user):
        cart = CartService(_make_auth_request(user))
        with pytest.raises(ValueError, match="[Ss]tock"):
            cart.add(product, quantity=product.stock + 99)

    def test_remove_deletes_db_row(self, product, user):
        from apps.cart.models import CartItem
        cart = CartService(_make_auth_request(user))
        cart.add(product, quantity=2)
        cart.remove(product)
        assert not CartItem.objects.filter(user=user, product=product).exists()

    def test_get_items_returns_price(self, product, user):
        cart = CartService(_make_auth_request(user))
        cart.add(product, quantity=1)
        items = cart.get_items()
        assert len(items) == 1
        assert items[0]["price"] == product.price

    def test_unit_price_uses_variant_price_when_variant_set(self, product, user):
        """Variante con precio distinto debe sobrescribir el precio base del producto."""
        variant = ProductVariant.objects.create(
            product=product, sku="VAR-PRICE-TEST",
            color="rojo", price=Decimal("99999"), stock=10,
        )
        cart = CartService(_make_auth_request(user))
        cart.add(product, quantity=1, variant=variant)
        items = cart.get_items()
        assert items[0]["price"] == Decimal("99999")


# ─── Variantes ────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCartServiceVariants:

    def test_same_product_different_variants_are_separate_lines(self, product, user):
        """Dos variantes del mismo producto → dos ítems independientes."""
        from apps.cart.models import CartItem
        v1 = ProductVariant.objects.create(
            product=product, sku="VAR-LINE-A", color="negro",
            price=300_000, stock=10,
        )
        v2 = ProductVariant.objects.create(
            product=product, sku="VAR-LINE-B", color="blanco",
            price=320_000, stock=10,
        )
        cart = CartService(_make_auth_request(user))
        cart.add(product, quantity=1, variant=v1)
        cart.add(product, quantity=2, variant=v2)
        assert cart.get_item_count() == 3
        assert CartItem.objects.filter(user=user).count() == 2

    def test_add_inactive_variant_raises(self, product, user):
        variant = ProductVariant.objects.create(
            product=product, sku="VAR-INACTIVE", color="verde",
            price=1, stock=10, is_active=False,
        )
        cart = CartService(_make_auth_request(user))
        with pytest.raises(ValueError, match="[Vv]ariante"):
            cart.add(product, quantity=1, variant=variant)

    def test_variant_stock_is_respected(self, product, user):
        variant = ProductVariant.objects.create(
            product=product, sku="VAR-STOCK", color="azul",
            price=1, stock=3,
        )
        cart = CartService(_make_auth_request(user))
        with pytest.raises(ValueError, match="[Ss]tock"):
            cart.add(product, quantity=4, variant=variant)


# ─── Merge sesión → DB ────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCartMerge:

    def test_session_items_merge_to_db_on_login(self, product, user):
        """
        Simula el flujo: agrega al carrito anónimo → hace login →
        los ítems deben aparecer en el carrito de BD del usuario.
        """
        from apps.cart.models import CartItem

        # 1. Agrega como anónimo
        anon_req = _make_anon_request()
        anon_cart = CartService(anon_req)
        anon_cart.add(product, quantity=3)

        # 2. "Hace login": copia la sesión al request autenticado
        auth_req = _make_auth_request(user)
        auth_req.session[anon_req.session.session_key] = None
        # Transfiere el estado de la sesión
        auth_req.session.update(dict(anon_req.session))
        auth_req.session.save()

        auth_cart = CartService(auth_req)
        auth_cart.merge_session_into_db()

        item = CartItem.objects.filter(user=user, product=product).first()
        assert item is not None
        assert item.quantity == 3
