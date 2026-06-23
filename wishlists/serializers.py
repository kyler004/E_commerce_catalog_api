from rest_framework import serializers

from wishlists.models import WishlistItem


class WishlistItemAddSerializer(serializers.Serializer):
    product = serializers.IntegerField()


class WishlistMoveToCartSerializer(serializers.Serializer):
    variant = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)


class WishlistProductSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)


class WishlistItemSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()

    class Meta:
        model = WishlistItem
        fields = ['id', 'product', 'added_at']

    def get_product(self, obj):
        return {
            'id': obj.product_id,
            'name': obj.product.name,
            'price': obj.product.price,
        }


class WishlistSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    items = WishlistItemSerializer(many=True)
    item_count = serializers.IntegerField()
    updated_at = serializers.DateTimeField()
