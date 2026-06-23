from django.contrib import admin

from .models import Promotion


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = (
        'code', 'discount_type', 'discount_value', 'is_active',
        'used_count', 'max_uses', 'valid_from', 'valid_until',
    )
    list_filter = ('is_active', 'discount_type')
    search_fields = ('code', 'description')
