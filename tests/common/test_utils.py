"""
Tests de utilidades comunes: generate_unique_slug, generate_order_code,
validate_file_extension, validate_file_size.
"""
import pytest
from django.core.exceptions import ValidationError
from unittest.mock import MagicMock

from apps.common.utils import generate_unique_slug, generate_order_code
from apps.common.validators import validate_file_extension, validate_file_size


# ─── Slug ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestGenerateUniqueSlug:

    def test_returns_slug_from_value(self, sub_category):
        from apps.catalog.models import Product
        slug = generate_unique_slug(Product, "Cámara IP Pro")
        assert slug == "camara-ip-pro"

    def test_returns_unique_slug_on_collision(self, product):
        from apps.catalog.models import Product
        # product.slug = "camara-ip-4mp" (desde conftest)
        slug = generate_unique_slug(Product, product.name)
        assert slug != product.slug
        assert slug.startswith(product.slug.rstrip("-"))


# ─── Order code ───────────────────────────────────────────────────────────────

def test_generate_order_code_default_prefix():
    code = generate_order_code()
    assert code.startswith("ORD-")
    assert len(code) > 6


def test_generate_order_code_custom_prefix():
    code = generate_order_code(prefix="ARES")
    assert code.startswith("ARES-")


def test_generate_order_code_is_unique():
    codes = {generate_order_code() for _ in range(50)}
    assert len(codes) == 50


# ─── Validators ───────────────────────────────────────────────────────────────

class TestValidateFileExtension:

    def _mock_file(self, filename):
        f = MagicMock()
        f.name = filename
        return f

    def test_allowed_extension_passes(self):
        validator = validate_file_extension(["jpg", "png"])
        validator(self._mock_file("photo.jpg"))   # no debe lanzar

    def test_forbidden_extension_raises(self):
        validator = validate_file_extension(["jpg", "png"])
        with pytest.raises(ValidationError):
            validator(self._mock_file("script.exe"))

    def test_case_insensitive(self):
        validator = validate_file_extension(["jpg", "png"])
        validator(self._mock_file("photo.JPG"))   # no debe lanzar


class TestValidateFileSize:

    def _mock_file(self, size_bytes):
        f = MagicMock()
        f.size = size_bytes
        return f

    def test_file_within_limit_passes(self):
        validator = validate_file_size(max_size_mb=2)
        validator(self._mock_file(1 * 1024 * 1024))   # 1 MB — no debe lanzar

    def test_file_at_exact_limit_passes(self):
        validator = validate_file_size(max_size_mb=2)
        validator(self._mock_file(2 * 1024 * 1024))   # exactamente 2 MB

    def test_file_over_limit_raises(self):
        validator = validate_file_size(max_size_mb=2)
        with pytest.raises(ValidationError):
            validator(self._mock_file(3 * 1024 * 1024))   # 3 MB
