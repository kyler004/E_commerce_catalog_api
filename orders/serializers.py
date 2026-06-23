from rest_framework import serializers

from orders.models import Order, OrderItem, ShippingAddress


class ShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = [
            'full_name',
            'address_line1',
            'address_line2',
            'city',
            'postal_code',
            'country',
            'phone',
        ]


class CheckoutSerializer(serializers.Serializer):
    shipping = ShippingAddressSerializer()


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            'id',
            'variant',
            'product_name',
            'sku',
            'size',
            'color',
            'quantity',
            'unit_price',
            'line_total',
        ]
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    shipping = ShippingAddressSerializer(source='shipping_address', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'status',
            'subtotal',
            'discount_amount',
            'promotion_code',
            'total',
            'items',
            'shipping',
            'created_at',
            'updated_at',
            'paid_at',
        ]
        read_only_fields = fields


class OrderListSerializer(serializers.ModelSerializer):
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'status', 'total', 'item_count', 'created_at', 'paid_at']

    def get_item_count(self, obj):
        return sum(item.quantity for item in obj.items.all())
