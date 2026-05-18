# beauty_shop/apps/catalog/views.py
from django.db.models import Q
from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404
from .models import Product, Category


# ========================
# 🛍️ Vista de listado de productos
# ========================
class ProductListView(ListView):
    model = Product
    template_name = 'catalog/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        """
        Catálogo unificado (productos + servicios) activos.

        Filtros (querystring):
          - ?tipo=product | service  -> filtra por item_type
          - ?q=texto                 -> busca en nombre/descripción
        Filtro por categoría (URL):
          - Categoría hoja  -> ítems asignados a ella.
          - Categoría raíz  -> ítems de la raíz O de sus subcategorías activas.
        """
        queryset = Product.objects.filter(is_active=True).select_related('category', 'brand')

        # Categoría por URL de ruta (/shop/categoria/<slug>/): 404 si no existe.
        url_slug = self.kwargs.get('category_slug')
        if url_slug:
            category = get_object_or_404(Category, slug=url_slug)
            queryset = queryset.filter(
                Q(category=category) | Q(category__parent=category)
            )

        # Categoría por querystring (?categoria=): lenient (no 404; vacío si no existe).
        qs_slug = self.request.GET.get('categoria')
        if qs_slug:
            category = Category.objects.filter(slug=qs_slug).first()
            queryset = queryset.filter(
                Q(category=category) | Q(category__parent=category)
            ) if category else queryset.none()

        tipo = self.request.GET.get('tipo')
        if tipo in ('product', 'service'):
            queryset = queryset.filter(item_type=tipo)

        q = self.request.GET.get('q', '').strip()
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q)
                | Q(description__icontains=q)
                | Q(subcategory__icontains=q)
            )

        return queryset

    def get_context_data(self, **kwargs):
        """Añade categorías (dinámicas desde la BD) y filtros activos."""
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()

        # Categorías con al menos 1 producto/servicio ACTIVO → 100% dinámicas.
        # Si se agrega una categoría nueva en Excel, aparece sola en los filtros.
        context['product_categories'] = (
            Category.objects.filter(
                products__item_type='product', products__is_active=True
            ).distinct().order_by('order', 'name')
        )
        context['service_categories'] = (
            Category.objects.filter(
                products__item_type='service', products__is_active=True
            ).distinct().order_by('order', 'name')
        )

        context['current_category'] = (
            self.kwargs.get('category_slug') or self.request.GET.get('categoria', '')
        )
        context['current_type'] = self.request.GET.get('tipo', '')
        context['search_query'] = self.request.GET.get('q', '').strip()
        return context


# ========================
# 🔍 Vista de detalle de producto
# ========================
class ProductDetailView(DetailView):
    model = Product
    template_name = 'catalog/product_detail.html'
    context_object_name = 'product'

    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related('category', 'brand')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        product = ctx['product']

        variants = list(product.variants.filter(is_active=True).order_by('color'))
        all_images = product.gallery_images()

        # Payload para el JS: lista plana de dicts. NO pre-serializar — el
        # tag |json_script ya codifica de forma segura (HTML-escape correcto).
        variants_payload = [{
            'id': v.id,
            'sku': v.sku,
            'color': v.color,
            'name': v.display_name,
            'price': float(v.price),
            'stock': v.stock,
            'images': product.images_for_color(v.color) if v.color else all_images,
        } for v in variants]

        ctx['variants'] = variants
        ctx['variants_payload'] = variants_payload
        ctx['all_images'] = all_images
        return ctx
