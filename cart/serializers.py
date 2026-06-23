from decimal import Decimal

from rest_framework import serializers

from cart.models import CartItem
from cart.services import get_available_quantity


class CartItemAddSerializer(serializers.Serializer):
    variant = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)


class CartItemUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)


class CartVariantSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    sku = serializers.CharField()
    size = serializers.CharField()
    color = serializers.CharField()
    product_name = serializers.CharField()
    available_quantity = serializers.IntegerField()


class CartItemSerializer(serializers.ModelSerializer):
    variant = serializers.SerializerMethodField()
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'variant', 'quantity', 'unit_price', 'line_total']

    def get_variant(self, obj):
        return {
            'id': obj.variant_id,
            'sku': obj.variant.sku,
            'size': obj.variant.size,
            'color': obj.variant.color,
            'product_name': obj.variant.product.name,
            'available_quantity': get_available_quantity(obj.variant),
        }

    def get_line_total(self, obj):
        return obj.unit_price * obj.quantity


class CartSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    items = CartItemSerializer(many=True)
    item_count = serializers.IntegerField()
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2)
    promotion = serializers.DictField(required=False, allow_null=True)
    updated_at = serializers.DateTimeField()
