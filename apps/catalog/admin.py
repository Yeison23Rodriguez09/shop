# securityshop/apps/catalog/admin.py
from django.contrib import admin
from .models import Category, Brand, Product


# ========================
# 📂 Admin de Categorías
# ========================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    ordering = ('name',)


# ========================
# 🏷️ Admin de Marcas
# ========================
@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'website')
    search_fields = ('name', 'country')
    ordering = ('name',)


# ========================
# 🛡️ Admin de Productos de Seguridad
# ========================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'item_type', 'model_number', 'price', 'stock',
        'category', 'brand', 'is_featured',
        'requires_installation', 'is_active', 'created_at'
    )
    list_filter = (
        'item_type', 'is_active', 'is_featured', 'requires_installation',
        'category', 'brand', 'created_at'
    )
    search_fields = ('name', 'description', 'model_number')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('-created_at',)
    autocomplete_fields = ('category', 'brand')
    filter_horizontal = ('compatible_with',)
    readonly_fields = ('created_at',)

    fieldsets = (
        ('Información general', {
            'fields': ('item_type', 'name', 'slug', 'category', 'brand', 'image', 'is_active', 'is_featured')
        }),
        ('Descripción y precio', {
            'fields': ('description', 'price', 'stock', 'specifications')
        }),
        ('Especificaciones técnicas', {
            'fields': (
                'model_number', 'warranty_months', 'resolution',
                'connectivity', 'power_supply', 'datasheet_url',
                'requires_installation'
            ),
            'classes': ('collapse',),
        }),
        ('Compatibilidad', {
            'fields': ('compatible_with',),
            'classes': ('collapse',),
        }),
        ('Metadatos', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
