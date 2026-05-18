"""
Tests HTTP del catálogo: listado, filtro por categoría y detalle de producto.
Verifican que las vistas devuelven 200 y renderizan el contenido correcto.
"""
import pytest
from django.urls import reverse

from apps.catalog.models import Category, Product


@pytest.mark.django_db
class TestProductListView:

    def test_product_list_returns_200(self, client, product):
        url = reverse("catalog:lista_productos")
        response = client.get(url)
        assert response.status_code == 200

    def test_product_list_shows_active_products(self, client, product):
        url = reverse("catalog:lista_productos")
        response = client.get(url)
        assert product.name.encode() in response.content

    def test_product_list_hides_inactive_products(self, client, sub_category):
        inactive = Product.objects.create(
            name="Producto Inactivo", slug="prod-inactivo",
            category=sub_category, price=100_000, stock=5, is_active=False,
        )
        url = reverse("catalog:lista_productos")
        response = client.get(url)
        assert inactive.name.encode() not in response.content

    def test_category_filter_shows_matching_products(self, client, product):
        url = reverse("catalog:product_by_category",
                      kwargs={"category_slug": product.category.slug})
        response = client.get(url)
        assert response.status_code == 200
        assert product.name.encode() in response.content

    def test_root_category_aggregates_subcategory_products(
        self, client, product, root_category
    ):
        """Productos de sub deben aparecer en la página de la categoría raíz."""
        url = reverse("catalog:product_by_category",
                      kwargs={"category_slug": root_category.slug})
        response = client.get(url)
        assert response.status_code == 200
        assert product.name.encode() in response.content

    def test_unknown_category_returns_404(self, client):
        url = reverse("catalog:product_by_category",
                      kwargs={"category_slug": "no-existe-jamas"})
        response = client.get(url)
        assert response.status_code == 404


@pytest.mark.django_db
class TestProductDetailView:

    def test_detail_returns_200(self, client, product):
        url = reverse("catalog:product_detail", kwargs={"slug": product.slug})
        response = client.get(url)
        assert response.status_code == 200

    def test_detail_shows_product_name(self, client, product):
        url = reverse("catalog:product_detail", kwargs={"slug": product.slug})
        response = client.get(url)
        assert product.name.encode() in response.content

    def test_detail_shows_price(self, client, product):
        url = reverse("catalog:product_detail", kwargs={"slug": product.slug})
        response = client.get(url)
        # El precio del fixture es 350_000; verificar que alguna parte del precio
        # aparece en el contenido (formateado o sin formato)
        price_prefix = str(int(product.price))[:3].encode()  # ej: b"350"
        assert price_prefix in response.content, \
            f"Precio {product.price} no renderiza en la PDP"

    def test_inactive_product_returns_404(self, client, product_no_stock):
        """Un producto inactivo no debe ser alcanzable por su URL."""
        inactive = product_no_stock
        inactive.is_active = False
        inactive.save()
        url = reverse("catalog:product_detail", kwargs={"slug": inactive.slug})
        response = client.get(url)
        assert response.status_code == 404

    def test_detail_unknown_slug_returns_404(self, client):
        url = reverse("catalog:product_detail", kwargs={"slug": "no-existe"})
        response = client.get(url)
        assert response.status_code == 404
