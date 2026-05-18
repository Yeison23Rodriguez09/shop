# beauty_shop\apps\catalog\services\product_services.py
from apps.catalog.models import Product, Category
from django.db.models import Q


# ========================
# 🔍 Búsqueda de productos
# ========================
def search_products(query):
    """
    Devuelve productos que coincidan con el título o descripción.
    """
    return Product.objects.filter(
        Q(name__icontains=query) |
        Q(description__icontains=query)
    ).distinct()


# ========================
# 📂 Productos por categoría
# ========================
def get_products_by_category(category_slug):
    """
    Devuelve productos activos dentro de una categoría.
    """
    return Product.objects.filter(
        category__slug=category_slug,
        is_active=True
    )


# ========================
# ⭐ Productos destacados
# ========================
def get_featured_products(limit=8):
    """
    Devuelve productos marcados como destacados.
    """
    return Product.objects.filter(is_featured=True, is_active=True)[:limit]


# ========================
# 🎯 Productos relacionados
# ========================
def get_related_products(product, limit=4):
    """
    Devuelve productos de la misma categoría excluyendo el actual.
    """
    return Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id)[:limit]
