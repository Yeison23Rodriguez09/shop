# config/urls.py
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

from apps.core.sitemaps import StaticViewSitemap, ProductSitemap, CategorySitemap

sitemaps = {
    'static': StaticViewSitemap,
    'products': ProductSitemap,
    'categories': CategorySitemap,
}

# ── Personalización del Django Admin ─────────────────────────
admin.site.site_header = 'Nexo YR Secure — Administración'
admin.site.site_title = 'Nexo YR Secure Admin'
admin.site.index_title = 'Panel de control de la tienda'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps},
         name='django.contrib.sitemaps.views.sitemap'),
    path('accounts/', include('allauth.urls')),
    path('', include('apps.core.urls', namespace='core')),
    path('cuentas/', include('apps.users.urls', namespace='users')),
    # Catálogo unificado (productos + servicios). Canónico en /shop/.
    path('shop/', include('apps.catalog.urls', namespace='catalog')),
    # Alias retrocompatible: /productos/ → /shop/
    path('productos/', RedirectView.as_view(url='/shop/', permanent=False)),
    path('carrito/', include('apps.cart.urls', namespace='cart')),
    path('pedidos/', include('apps.orders.urls', namespace='orders')),
    path('pagos/', include('apps.payments.urls', namespace='payments')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
