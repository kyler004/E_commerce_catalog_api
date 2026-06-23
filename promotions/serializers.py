from rest_framework import serializers

from promotions.models import Promotion


class PromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promotion
        fields = [
            'id',
            'code',
            'description',
            'discount_type',
            'discount_value',
            'min_order_amount',
            'max_uses',
            'used_count',
            'valid_from',
            'valid_until',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['used_count', 'created_at', 'updated_at']

    def validate_code(self, value):
        return value.upper()


class ApplyPromoSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50)
