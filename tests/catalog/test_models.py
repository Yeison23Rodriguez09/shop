"""
Tests de modelos del catálogo: Category, Product, ProductVariant.

Cubren: propiedades calculadas, auto-slug, validaciones de dominio y
la relación variante <-> producto que es central en el sistema de inventario.
"""
import pytest

from apps.catalog.models import Category, Product, ProductVariant


# ─── Category ────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCategoryModel:

    def test_slug_auto_generated_on_save(self):
        cat = Category.objects.create(name="Cámaras IP")
        assert cat.slug == "camaras-ip"

    def test_explicit_slug_not_overwritten(self):
        cat = Category.objects.create(name="Cámaras IP 2", slug="custom-slug")
        assert cat.slug == "custom-slug"

    def test_is_root_without_parent(self):
        cat = Category.objects.create(name="CCTV Root", slug="cctv-root")
        assert cat.is_root is True

    def test_is_root_false_with_parent(self, root_category):
        sub = Category.objects.create(name="Sub", slug="sub-root", parent=root_category)
        assert sub.is_root is False

    def test_full_path_root(self):
        cat = Category.objects.create(name="CCTV Path", slug="cctv-path")
        assert cat.full_path == "CCTV Path"

    def test_full_path_nested(self, root_category):
        sub = Category.objects.create(name="Cámaras IP", slug="cam-ip-path",
                                      parent=root_category)
        assert sub.full_path == f"{root_category.name} / Cámaras IP"

    def test_str_includes_parent_arrow(self, root_category):
        sub = Category.objects.create(name="Sub Str", slug="sub-str",
                                      parent=root_category)
        assert "→" in str(sub)
        assert root_category.name in str(sub)


# ─── Product ─────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestProductModel:

    def test_slug_auto_generated(self, sub_category):
        p = Product.objects.create(name="Sensor PIR Test", slug="",
                                   category=sub_category, price=80_000, stock=5)
        assert p.slug == "sensor-pir-test"

    def test_warranty_label_years(self, sub_category):
        p = Product.objects.create(name="Cam Warranty A", slug="cam-warranty-a",
                                   category=sub_category, price=1, stock=1,
                                   warranty_months=12)
        assert p.warranty_label == "1 año"

    def test_warranty_label_two_years(self, sub_category):
        p = Product.objects.create(name="Cam Warranty B", slug="cam-warranty-b",
                                   category=sub_category, price=1, stock=1,
                                   warranty_months=24)
        assert p.warranty_label == "2 años"

    def test_warranty_label_months(self, sub_category):
        p = Product.objects.create(name="Cam Warranty C", slug="cam-warranty-c",
                                   category=sub_category, price=1, stock=1,
                                   warranty_months=6)
        assert p.warranty_label == "6 meses"

    def test_warranty_label_one_month(self, sub_category):
        p = Product.objects.create(name="Cam Warranty D", slug="cam-warranty-d",
                                   category=sub_category, price=1, stock=1,
                                   warranty_months=1)
        assert p.warranty_label == "1 mes"

    def test_str_returns_name(self, product):
        assert str(product) == product.name

    def test_gallery_images_empty_when_no_dir(self, product):
        """Sin carpeta en disco, gallery_images devuelve lista vacía."""
        assert product.gallery_images() == []

    def test_images_for_color_returns_all_on_empty_color(self, product):
        """Con color vacío e imágenes vacías, devuelve lista vacía (fallback galería)."""
        assert product.images_for_color("") == []


# ─── ProductVariant ───────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestProductVariantModel:

    def test_unique_sku(self, product):
        ProductVariant.objects.create(
            product=product, sku="SKU-UNIQUE-001",
            color="negro", price=350_000, stock=10,
        )
        with pytest.raises(Exception):   # IntegrityError vía unique constraint
            ProductVariant.objects.create(
                product=product, sku="SKU-UNIQUE-001",
                color="blanco", price=350_000, stock=5,
            )

    def test_unique_together_product_color(self, product):
        ProductVariant.objects.create(
            product=product, sku="SKU-COLOR-A", color="negro",
            price=350_000, stock=10,
        )
        with pytest.raises(Exception):
            ProductVariant.objects.create(
                product=product, sku="SKU-COLOR-B", color="negro",
                price=300_000, stock=3,
            )

    def test_display_name_uses_color_when_no_explicit_name(self, product):
        v = ProductVariant(product=product, sku="V-DISP-1",
                           color="rojo", price=1, stock=1)
        assert "rojo" in v.display_name.lower()

    def test_display_name_uses_explicit_name(self, product):
        v = ProductVariant(product=product, sku="V-DISP-2", color="rojo",
                           name="Edición Especial Roja", price=1, stock=1)
        assert v.display_name == "Edición Especial Roja"

    def test_str_includes_sku_and_color(self, product):
        v = ProductVariant(product=product, sku="V-STR-1",
                           color="azul", price=1, stock=1)
        assert "V-STR-1" in str(v)
        assert "azul" in str(v)
