# beauty_shop\apps\common\context_processors.py
"""
Context processors globales.

Exponen en TODOS los templates:
  - menu_categories          -> categorias raiz activas con hijos prefetch
  - menu_service_categories  -> categorias de servicios con servicios prefetch
  - active_category_slug     -> slug actual (si la URL trae `category_slug`)
  - shop_*                   -> datos del comerciante desde .env
  - CART_SESSION_ID

Cada raiz queda anotada con `is_current_branch` (bool) para que las plantillas
puedan auto-abrir el `<details>` del arbol activo sin logica fea en el HTML.
"""
import os
from django.conf import settings
from django.db.models import Prefetch

from apps.catalog.models import Category, Product


def _active_slug(request) -> str:
    rm = getattr(request, 'resolver_match', None)
    if not rm:
        return ''
    return rm.kwargs.get('category_slug') or rm.kwargs.get('slug') or ''


def categories_processor(request):
    """Categorias raiz activas + subcategorias prefetch + flag de rama actual."""
    active_subs = Category.objects.filter(is_active=True).order_by('order', 'name')
    roots = list(
        Category.objects
        .filter(is_active=True, parent__isnull=True)
        .order_by('order', 'name')
        .prefetch_related(Prefetch('children', queryset=active_subs, to_attr='children_active'))
    )

    active = _active_slug(request)
    for root in roots:
        sub_slugs = {s.slug for s in getattr(root, 'children_active', [])}
        root.is_current_branch = bool(active) and (active == root.slug or active in sub_slugs)

    return {
        'menu_categories': roots,
        'active_category_slug': active,
    }


def service_categories_processor(request):
    """
    Catálogo unificado: los "servicios" son Product con item_type='service'.
    Devuelve las categorías que contienen al menos un servicio activo, cada
    una anotada con `.services_active` (lista de esos servicios) para que el
    navbar/home rendericen el submenú de servicios sin la app services.
    """
    active_services = Product.objects.filter(
        is_active=True, item_type='service'
    ).order_by('name')

    cats = list(
        Category.objects
        .filter(is_active=True)
        .order_by('order', 'name')
        .prefetch_related(Prefetch('products', queryset=active_services, to_attr='services_active'))
    )
    cats = [c for c in cats if getattr(c, 'services_active', [])]

    active = _active_slug(request)
    for cat in cats:
        svc_slugs = {s.slug for s in getattr(cat, 'services_active', [])}
        cat.is_current_branch = bool(active) and (active == cat.slug or active in svc_slugs)

    # ── Grupos para el dropdown SHOP del navbar ──────────────────────
    # Categorías distintas que tienen al menos 1 producto / servicio activo.
    prod_cat_ids = (
        Product.objects.filter(is_active=True, item_type='product')
        .values_list('category_id', flat=True).distinct()
    )
    svc_cat_ids = (
        Product.objects.filter(is_active=True, item_type='service')
        .values_list('category_id', flat=True).distinct()
    )
    nav_product_categories = list(
        Category.objects.filter(id__in=prod_cat_ids).order_by('order', 'name')
    )
    nav_service_categories = list(
        Category.objects.filter(id__in=svc_cat_ids).order_by('order', 'name')
    )

    return {
        'menu_service_categories': cats,
        'nav_product_categories': nav_product_categories,
        'nav_service_categories': nav_service_categories,
    }


def cart_session_id(request):
    """Devuelve el ID de sesion del carrito, configurable desde settings."""
    return {'CART_SESSION_ID': getattr(settings, 'CART_SESSION_ID', 'cart')}


def cart_summary(request):
    """
    Expone `cart_count` (numero total de unidades) y `cart_total` (Decimal)
    para el badge en navbar y mini-cart. Tolerante a errores: si algo falla
    (sesion no inicializada, request sin sesion en tests, etc.) devuelve 0.
    """
    try:
        from apps.cart.services import CartService
        cart = CartService(request)
        return {
            'cart_count': cart.get_item_count(),
            'cart_total': cart.get_total_price(),
        }
    except Exception:
        return {'cart_count': 0, 'cart_total': 0}


def shop_info(request):
    """Datos del comerciante (.env) disponibles en todas las plantillas."""
    return {
        'shop_name': os.getenv('SHOP_NAME', 'Nexo YR Secure'),
        'shop_bank_name': os.getenv('SHOP_BANK_NAME', '—'),
        'shop_bank_account_number': os.getenv('SHOP_BANK_ACCOUNT_NUMBER', '—'),
        'shop_bank_account_type': os.getenv('SHOP_BANK_ACCOUNT_TYPE', 'Ahorros'),
        'shop_bank_holder_name': os.getenv('SHOP_BANK_HOLDER_NAME', '—'),
        'shop_bank_holder_id': os.getenv('SHOP_BANK_HOLDER_ID', '—'),
        'shop_contact_phone': os.getenv('SHOP_CONTACT_PHONE', '—'),
        'shop_contact_email': os.getenv('SHOP_CONTACT_EMAIL', 'contacto@example.com'),
        'google_analytics_id': os.getenv('GOOGLE_ANALYTICS_ID', ''),
    }
