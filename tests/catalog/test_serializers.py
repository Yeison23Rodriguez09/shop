"""
Tests de serializers DRF del catálogo.
Verifica que los serializadores producen la forma esperada para la API.
"""
import pytest
from decimal import Decimal

from apps.catalog.models import Brand
from apps.catalog.serializers import ProductSerializer, CategorySerializer


@pytest.mark.django_db
class TestProductSerializer:

    def test_serializes_required_fields(self, product):
        data = ProductSerializer(product).data
        for field in ("id", "name", "slug", "price", "is_active"):
            assert field in data, f"Campo '{field}' ausente en serializer"

    def test_price_is_correct_value(self, product):
        """El precio serializado debe representar el mismo valor que el modelo."""
        from decimal import Decimal
        data = ProductSerializer(product).data
        assert Decimal(data["price"]) == product.price

    def test_category_nested(self, product):
        data = ProductSerializer(product).data
        assert data["category"]["slug"] == product.category.slug
        assert data["category"]["name"] == product.category.name

    def test_brand_nested_none_when_no_brand(self, product):
        product.brand = None
        product.save()
        data = ProductSerializer(product).data
        assert data["brand"] is None

    def test_brand_nested_when_set(self, product, sub_category):
        brand = Brand.objects.create(name="TestBrand")
        product.brand = brand
        product.save()
        data = ProductSerializer(product).data
        assert data["brand"]["name"] == "TestBrand"


@pytest.mark.django_db
class TestCategorySerializer:

    def test_serializes_id_name_slug(self, root_category):
        data = CategorySerializer(root_category).data
        assert data["id"] == root_category.id
        assert data["name"] == root_category.name
        assert data["slug"] == root_category.slug
