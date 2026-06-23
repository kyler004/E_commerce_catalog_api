from decimal import Decimal

from django.db.models import Sum, F
from django.utils import timezone

from api.models import Variant
from cart.models import Cart, CartItem


class CartValidationError(Exception):
    pass


def get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def get_available_quantity(variant):
    try:
        return variant.inventory.quantity
    except Variant.inventory.RelatedObjectDoesNotExist:
        return 0


def validate_quantity(variant, quantity):
    if quantity < 1:
        raise CartValidationError('Quantity must be at least 1.')
    available = get_available_quantity(variant)
    if quantity > available:
        raise CartValidationError(f'Insufficient stock. Available: {available}.')


def _touch_cart(cart):
    cart.updated_at = timezone.now()
    cart.save(update_fields=['updated_at'])


def add_item(user, variant_id, quantity=1):
    cart = get_or_create_cart(user)
    try:
        variant = Variant.objects.select_related('product', 'inventory').get(pk=variant_id)
    except Variant.DoesNotExist as exc:
        raise CartValidationError('Variant not found.') from exc

    item = CartItem.objects.filter(cart=cart, variant=variant).first()
    new_quantity = quantity if item is None else item.quantity + quantity
    validate_quantity(variant, new_quantity)

    unit_price = variant.product.price
    if item is None:
        item = CartItem.objects.create(
            cart=cart,
            variant=variant,
            quantity=quantity,
            unit_price=unit_price,
        )
        created = True
    else:
        item.quantity = new_quantity
        item.unit_price = unit_price
        item.save(update_fields=['quantity', 'unit_price', 'updated_at'])
        created = False

    _touch_cart(cart)
    return item, created


def update_item(user, item_id, quantity):
    cart = get_or_create_cart(user)
    try:
        item = CartItem.objects.select_related(
            'variant__product', 'variant__inventory'
        ).get(pk=item_id, cart=cart)
    except CartItem.DoesNotExist as exc:
        raise CartItem.DoesNotExist from exc

    validate_quantity(item.variant, quantity)
    item.quantity = quantity
    item.unit_price = item.variant.product.price
    item.save(update_fields=['quantity', 'unit_price', 'updated_at'])
    _touch_cart(cart)
    return item


def remove_item(user, item_id):
    cart = get_or_create_cart(user)
    try:
        item = CartItem.objects.get(pk=item_id, cart=cart)
    except CartItem.DoesNotExist as exc:
        raise CartItem.DoesNotExist from exc
    item.delete()
    _touch_cart(cart)


def clear_cart(user):
    cart = get_or_create_cart(user)
    cart.items.all().delete()
    _touch_cart(cart)
    return cart


def compute_cart_summary(cart):
    aggregates = cart.items.aggregate(
        item_count=Sum('quantity'),
        subtotal=Sum(F('unit_price') * F('quantity')),
    )
    return {
        'item_count': aggregates['item_count'] or 0,
        'subtotal': aggregates['subtotal'] or Decimal('0.00'),
    }
