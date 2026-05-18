from django.urls import path
from .views import (
    CartDetailView,
    AddToCartView,
    UpdateCartView,
    RemoveFromCartView,
    ClearCartView,
)

app_name = 'cart'

urlpatterns = [
    path('', CartDetailView.as_view(), name='cart_detail'),
    path('add/<int:product_id>/', AddToCartView.as_view(), name='add_to_cart'),
    path('update/<int:product_id>/', UpdateCartView.as_view(), name='update'),
    path('remove/<int:product_id>/', RemoveFromCartView.as_view(), name='remove'),
    path('clear/', ClearCartView.as_view(), name='clear'),
]
