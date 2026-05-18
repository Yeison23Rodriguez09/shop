# beauty_shop/apps/catalog/serializers.py
from rest_framework import serializers
from .models import Product, Category, Brand


# ========================
# 📂 Categoría
# ========================
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


# ========================
# 🏷️ Marca
# ========================
class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name']


# ========================
# 🛍️ Producto
# ========================
class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'price',
            'image',
            'category',
            'brand',
            'is_active',
            'created_at',
        ]
