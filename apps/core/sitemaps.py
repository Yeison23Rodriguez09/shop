# apps/core/sitemaps.py
#
# Sitemaps para acelerar la indexación en Google. Se exponen en /sitemap.xml
# (ver config/urls.py). El dominio lo aporta django.contrib.sites (SITE_ID=1).
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.catalog.models import Product, Category


class StaticViewSitemap(Sitemap):
    """Páginas estáticas clave para la conversión (home, catálogo, contacto)."""
    priority = 0.8
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        return ['core:home', 'catalog:product_list', 'core:contact']

    def location(self, item):
        return reverse(item)


class ProductSitemap(Sitemap):
    """Productos y servicios activos del catálogo."""
    priority = 0.7
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        return Product.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.created_at

    def location(self, obj):
        return reverse('catalog:product_detail', kwargs={'slug': obj.slug})


class CategorySitemap(Sitemap):
    """Categorías activas del catálogo."""
    priority = 0.6
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        return Category.objects.filter(is_active=True)

    def location(self, obj):
        return reverse('catalog:product_by_category', kwargs={'category_slug': obj.slug})
