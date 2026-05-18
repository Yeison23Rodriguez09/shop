# beauty_shop/apps/catalog/urls.py
from django.urls import path
from .views import ProductListView, ProductDetailView

app_name = 'catalog'

urlpatterns = [
    # Listado de productos - se exponen dos alias para que tanto los templates
    # antiguos ('lista_productos') como las views nuevas ('product_list')
    # puedan resolverlo via {% url %} y reverse().
    path('', ProductListView.as_view(), name='product_list'),
    path('', ProductListView.as_view(), name='lista_productos'),

    path('categoria/<slug:category_slug>/', ProductListView.as_view(), name='product_by_category'),
    path('producto/<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),
]
