from rest_framework import serializers
from .models import Category, Product, Variant, Inventory

class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = ['quantity', 'last_updated']

class VariantSerializer(serializers.ModelSerializer):
    inventory = InventorySerializer(read_only=True)  # Nested serializer for related inventory

    class Meta:
        model = Variant
        fields = ['id', 'size', 'color', 'sku', 'inventory']

class ProductSerializer(serializers.ModelSerializer):
    variants = VariantSerializer(many=True, read_only=True)  # Nested list of variants

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'category', 'created_at', 'variants']

class CategorySerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)  # Nested products for category

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'parent', 'products']