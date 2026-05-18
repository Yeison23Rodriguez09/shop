"""
conftest.py — fixtures globales de pytest para Ares Shop.

Disponibles en todos los módulos de tests sin necesidad de importar.
"""
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


# ─── Usuarios ────────────────────────────────────────────────────────────────

@pytest.fixture
def user(db):
    """Usuario autenticado estándar."""
    return User.objects.create_user(
        email="test@aresseguridad.com",
        username="testuser",
        password="TestPass123!",
    )


@pytest.fixture
def admin_user(db):
    """Superusuario para tests de admin."""
    return User.objects.create_superuser(
        email="admin@aresseguridad.com",
        username="adminuser",
        password="AdminPass123!",
    )


@pytest.fixture
def authenticated_client(client, user):
    """Client de Django con sesión iniciada."""
    client.force_login(user)
    return client


# ─── Catálogo ────────────────────────────────────────────────────────────────

@pytest.fixture
def root_category(db):
    """Categoría raíz de prueba."""
    from apps.catalog.models import Category
    return Category.objects.create(
        name="CCTV",
        slug="cctv",
        is_active=True,
    )


@pytest.fixture
def sub_category(db, root_category):
    """Subcategoría de prueba."""
    from apps.catalog.models import Category
    return Category.objects.create(
        name="Cámaras IP",
        slug="camaras-ip",
        parent=root_category,
        is_active=True,
    )


@pytest.fixture
def product(db, sub_category):
    """Producto de prueba con stock."""
    from apps.catalog.models import Product
    return Product.objects.create(
        name="Cámara IP 4MP",
        slug="camara-ip-4mp",
        category=sub_category,
        price=350_000,
        stock=20,
        is_active=True,
    )


@pytest.fixture
def product_no_stock(db, sub_category):
    """Producto sin stock."""
    from apps.catalog.models import Product
    return Product.objects.create(
        name="Cámara Agotada",
        slug="camara-agotada",
        category=sub_category,
        price=100_000,
        stock=0,
        is_active=True,
    )
