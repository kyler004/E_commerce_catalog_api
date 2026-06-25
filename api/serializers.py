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
        fields = ['id', 'product', 'size', 'color', 'sku', 'inventory']

class ProductSerializer(serializers.ModelSerializer):
    variants = VariantSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'category', 'image_url', 'created_at',
            'variants', 'average_rating', 'review_count',
        ]

    def get_average_rating(self, obj):
        rating = getattr(obj, 'average_rating', None)
        if rating is not None:
            return round(float(rating), 2)
        from reviews.services import get_product_rating_summary
        return get_product_rating_summary(obj)['average_rating']

    def get_review_count(self, obj):
        count = getattr(obj, 'review_count', None)
        if count is not None:
            return count
        from reviews.services import get_product_rating_summary
        return get_product_rating_summary(obj)['review_count']

class CategorySerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)  # Nested products for category

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'parent', 'products']