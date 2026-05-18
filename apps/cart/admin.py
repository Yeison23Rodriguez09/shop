# apps/cart/admin.py
from django.contrib import admin
from .models import CartItem


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """Visualización de los carritos persistentes de usuarios autenticados."""
    list_display = ('id', 'user', 'product', 'quantity', 'subtotal_display', 'updated_at')
    list_filter = ('added_at', 'updated_at')
    search_fields = ('user__email', 'product__name')
    autocomplete_fields = ('user', 'product')
    readonly_fields = ('added_at', 'updated_at')
    ordering = ('-updated_at',)

    def subtotal_display(self, obj):
        return f'${obj.subtotal:,.0f}'
    subtotal_display.short_description = 'Subtotal'
