from decimal import Decimal
from datetime import datetime

from django.db.models import Count, Sum
from django.db.models.functions import Coalesce, TruncMonth
from django.db import transaction
from django.utils import timezone

from api.models import Inventory
from cart.services import (
    CartValidationError,
    clear_cart,
    compute_cart_summary,
    get_or_create_cart,
    validate_quantity,
)
from orders.models import Order, OrderItem, ShippingAddress
from promotions.services import (
    PromotionError,
    increment_promotion_usage,
    resolve_promotion_for_checkout,
)


class OrderValidationError(Exception):
    pass


class OrderNotFoundError(Exception):
    pass


class OrderStateError(Exception):
    pass


def get_user_orders(user):
    return (
        Order.objects.filter(user=user)
        .prefetch_related('items', 'shipping_address')
    )


def filter_user_orders(user, filters):
    queryset = get_user_orders(user)
    if filters.get('status'):
        queryset = queryset.filter(status=filters['status'])

    paid_after = filters.get('paid_after')
    if paid_after:
        queryset = queryset.annotate(paid_timestamp=Coalesce('paid_at', 'created_at'))
        queryset = queryset.filter(paid_timestamp__gte=paid_after)

    paid_before = filters.get('paid_before')
    if paid_before:
        queryset = queryset.annotate(paid_timestamp=Coalesce('paid_at', 'created_at'))
        queryset = queryset.filter(paid_timestamp__lte=paid_before)

    created_after = filters.get('created_after')
    if created_after:
        queryset = queryset.filter(created_at__gte=created_after)

    created_before = filters.get('created_before')
    if created_before:
        queryset = queryset.filter(created_at__lte=created_before)

    ordering = filters.get('ordering')
    if ordering:
        queryset = queryset.order_by(ordering)

    return queryset


def get_user_order(user, order_id):
    try:
        return get_user_orders(user).get(pk=order_id)
    except Order.DoesNotExist as exc:
        raise OrderNotFoundError from exc


@transaction.atomic
def checkout(user, shipping_data):
    cart = get_or_create_cart(user)
    cart_items = list(
        cart.items.select_related('variant__product', 'variant__inventory')
    )
    if not cart_items:
        raise OrderValidationError('Cart is empty.')

    for item in cart_items:
        try:
            validate_quantity(item.variant, item.quantity)
        except CartValidationError as exc:
            raise OrderValidationError(str(exc)) from exc

    summary = compute_cart_summary(cart)
    promotion_code = ''
    discount_amount = Decimal('0.00')
    if cart.applied_promotion_id is not None:
        try:
            promotion_code, discount_amount = resolve_promotion_for_checkout(
                cart, summary['subtotal']
            )
        except PromotionError as exc:
            raise OrderValidationError(str(exc)) from exc

    total = max(summary['subtotal'] - discount_amount, Decimal('0.00'))
    order = Order.objects.create(
        user=user,
        status=Order.Status.PENDING,
        subtotal=summary['subtotal'],
        discount_amount=discount_amount,
        promotion_code=promotion_code,
        total=total,
    )

    ShippingAddress.objects.create(order=order, **shipping_data)

    order_items = []
    for item in cart_items:
        variant = item.variant
        category = variant.product.category
        line_total = item.unit_price * item.quantity
        order_items.append(
            OrderItem(
                order=order,
                variant=variant,
                product_name=variant.product.name,
                sku=variant.sku,
                size=variant.size,
                color=variant.color,
                category_id=category.id,
                category_name=category.name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                line_total=line_total,
            )
        )
    OrderItem.objects.bulk_create(order_items)

    clear_cart(user)
    return get_user_order(user, order.pk)


@transaction.atomic
def confirm_payment(user, order_id):
    try:
        order = (
            Order.objects.select_for_update()
            .prefetch_related('items__variant')
            .get(pk=order_id, user=user)
        )
    except Order.DoesNotExist as exc:
        raise OrderNotFoundError from exc

    if order.status != Order.Status.PENDING:
        raise OrderStateError('Only pending orders can be paid.')

    variant_ids = [
        item.variant_id for item in order.items.all() if item.variant_id is not None
    ]
    inventories = {
        inv.variant_id: inv
        for inv in Inventory.objects.select_for_update().filter(variant_id__in=variant_ids)
    }

    for item in order.items.all():
        if item.variant_id is None:
            raise OrderValidationError(f'Variant for SKU {item.sku} is no longer available.')
        inventory = inventories.get(item.variant_id)
        available = inventory.quantity if inventory else 0
        if item.quantity > available:
            raise OrderValidationError(
                f'Insufficient stock for {item.sku}. Available: {available}.'
            )

    for item in order.items.all():
        inventory = inventories[item.variant_id]
        inventory.quantity -= item.quantity
        inventory.save(update_fields=['quantity', 'last_updated'])

    if order.promotion_code:
        try:
            increment_promotion_usage(order.promotion_code)
        except PromotionError as exc:
            raise OrderValidationError(str(exc)) from exc

    order.status = Order.Status.PAID
    order.paid_at = timezone.now()
    order.save(update_fields=['status', 'paid_at', 'updated_at'])
    return get_user_order(user, order.pk)


@transaction.atomic
def cancel_order(user, order_id):
    try:
        order = Order.objects.select_for_update().get(pk=order_id, user=user)
    except Order.DoesNotExist as exc:
        raise OrderNotFoundError from exc

    if order.status != Order.Status.PENDING:
        raise OrderStateError('Only pending orders can be cancelled.')

    order.status = Order.Status.CANCELLED
    order.save(update_fields=['status', 'updated_at'])
    return get_user_order(user, order.pk)


def get_receipt_order(user, order_id):
    order = get_user_order(user, order_id)
    if order.status != Order.Status.PAID:
        raise OrderStateError('Receipts are only available for paid orders.')
    return order


def _decimal_string(value):
    return str((value or Decimal('0.00')).quantize(Decimal('0.01')))


def _period_start(period):
    if period == 'all':
        return None

    months = int(period[:-1])
    now = timezone.now()
    year = now.year
    month = now.month - months + 1
    while month <= 0:
        year -= 1
        month += 12
    return datetime(year, month, 1, tzinfo=timezone.get_current_timezone())


def get_spending_summary(user, period='12m'):
    paid_orders = Order.objects.filter(user=user, status=Order.Status.PAID)
    status_counts = (
        Order.objects.filter(user=user)
        .values('status')
        .annotate(count=Count('id'))
    )
    counts_by_status = {row['status']: row['count'] for row in status_counts}

    paid_aggregates = paid_orders.aggregate(
        lifetime_spend=Sum('total'),
        total_savings=Sum('discount_amount'),
        paid_order_count=Count('id'),
    )
    paid_order_count = paid_aggregates['paid_order_count'] or 0
    lifetime_spend = paid_aggregates['lifetime_spend'] or Decimal('0.00')
    average_order_value = (
        lifetime_spend / paid_order_count if paid_order_count else Decimal('0.00')
    )

    period_orders = paid_orders.annotate(
        paid_timestamp=Coalesce('paid_at', 'created_at')
    )
    start = _period_start(period)
    if start is not None:
        period_orders = period_orders.filter(paid_timestamp__gte=start)

    spending_by_month = [
        {
            'period': row['period'].strftime('%Y-%m'),
            'total': _decimal_string(row['total']),
            'order_count': row['order_count'],
        }
        for row in (
            period_orders.annotate(period=TruncMonth('paid_timestamp'))
            .values('period')
            .annotate(total=Sum('total'), order_count=Count('id'))
            .order_by('period')
        )
    ]

    period_order_ids = period_orders.values('id')
    spending_by_category = [
        {
            'category_id': row['category_id'],
            'category_name': row['category_name'],
            'total': _decimal_string(row['total']),
            'order_count': row['order_count'],
        }
        for row in (
            OrderItem.objects.filter(
                order_id__in=period_order_ids,
                category_id__isnull=False,
            )
            .values('category_id', 'category_name')
            .annotate(total=Sum('line_total'), order_count=Count('order', distinct=True))
            .order_by('-total', 'category_name')
        )
    ]

    recent_paid_orders = []
    for order in paid_orders.prefetch_related('items').order_by('-paid_at', '-created_at')[:5]:
        paid_timestamp = order.paid_at or order.created_at
        recent_paid_orders.append(
            {
                'id': order.id,
                'total': _decimal_string(order.total),
                'paid_at': paid_timestamp.isoformat().replace('+00:00', 'Z'),
                'item_count': sum(item.quantity for item in order.items.all()),
            }
        )

    return {
        'currency': 'USD',
        'lifetime_spend': _decimal_string(lifetime_spend),
        'paid_order_count': paid_order_count,
        'pending_order_count': counts_by_status.get(Order.Status.PENDING, 0),
        'cancelled_order_count': counts_by_status.get(Order.Status.CANCELLED, 0),
        'total_savings': _decimal_string(paid_aggregates['total_savings']),
        'average_order_value': _decimal_string(average_order_value),
        'spending_by_month': spending_by_month,
        'spending_by_category': spending_by_category,
        'recent_paid_orders': recent_paid_orders,
    }
