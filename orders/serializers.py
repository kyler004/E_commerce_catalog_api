import re

from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import serializers

from orders.models import Order, OrderItem, ShippingAddress


def parse_datetime_query_param(value):
    parsed_datetime = parse_datetime(value)
    if parsed_datetime is not None:
        if timezone.is_naive(parsed_datetime):
            parsed_datetime = timezone.make_aware(parsed_datetime)
        return parsed_datetime

    parsed_date = parse_date(value)
    if parsed_date is None:
        raise serializers.ValidationError('Use YYYY-MM-DD or an ISO 8601 datetime.')

    return parsed_date


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
            'category_id',
            'category_name',
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


class OrderListQuerySerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.Status.values, required=False)
    ordering = serializers.ChoiceField(
        choices=['-paid_at', '-created_at', '-total'],
        required=False,
    )
    paid_after = serializers.CharField(required=False)
    paid_before = serializers.CharField(required=False)
    created_after = serializers.CharField(required=False)
    created_before = serializers.CharField(required=False)

    def validate(self, attrs):
        for field in (
            'paid_after',
            'paid_before',
            'created_after',
            'created_before',
        ):
            if field in attrs:
                attrs[field] = parse_datetime_query_param(attrs[field])
        return attrs


class SpendingSummaryQuerySerializer(serializers.Serializer):
    period = serializers.CharField(required=False, default='12m')

    def validate_period(self, value):
        if value == 'all':
            return value
        if not re.fullmatch(r'[1-9]\d*m', value):
            raise serializers.ValidationError('Use a month period like 12m, or all.')
        return value
