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
    order = Order.objects.create(
        user=user,
        status=Order.Status.PENDING,
        subtotal=summary['subtotal'],
        total=summary['subtotal'],
    )

    ShippingAddress.objects.create(order=order, **shipping_data)

    order_items = []
    for item in cart_items:
        variant = item.variant
        line_total = item.unit_price * item.quantity
        order_items.append(
            OrderItem(
                order=order,
                variant=variant,
                product_name=variant.product.name,
                sku=variant.sku,
                size=variant.size,
                color=variant.color,
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
