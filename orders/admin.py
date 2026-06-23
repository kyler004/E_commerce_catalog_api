from django.contrib import admin

from .models import Order, OrderItem, ShippingAddress


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
        'variant', 'product_name', 'sku', 'size', 'color',
        'quantity', 'unit_price', 'line_total',
    )


class ShippingAddressInline(admin.StackedInline):
    model = ShippingAddress
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total', 'created_at', 'paid_at')
    list_filter = ('status',)
    search_fields = ('user__email',)
    readonly_fields = ('subtotal', 'total', 'created_at', 'updated_at', 'paid_at')
    inlines = [OrderItemInline, ShippingAddressInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'sku', 'product_name', 'quantity', 'unit_price', 'line_total')
    readonly_fields = (
        'order', 'variant', 'product_name', 'sku', 'size', 'color',
        'quantity', 'unit_price', 'line_total',
    )
