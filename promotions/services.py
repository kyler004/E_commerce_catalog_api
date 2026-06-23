from decimal import Decimal

from django.utils import timezone

from promotions.models import Promotion


class PromotionError(Exception):
    pass


def get_promotion_by_code(code):
    try:
        return Promotion.objects.get(code=code.upper())
    except Promotion.DoesNotExist as exc:
        raise PromotionError('Invalid promotion code.') from exc


def validate_promotion(promotion, subtotal):
    if not promotion.is_active:
        raise PromotionError('This promotion is not active.')
    if not promotion.is_within_date_range():
        raise PromotionError('This promotion is not currently valid.')
    if promotion.min_order_amount is not None and subtotal < promotion.min_order_amount:
        raise PromotionError(
            f'Minimum order amount of {promotion.min_order_amount} required.'
        )
    if promotion.max_uses is not None and promotion.used_count >= promotion.max_uses:
        raise PromotionError('This promotion has reached its usage limit.')


def calculate_discount(promotion, subtotal):
    if promotion.discount_type == Promotion.DiscountType.PERCENTAGE:
        discount = (subtotal * promotion.discount_value / Decimal('100')).quantize(Decimal('0.01'))
    else:
        discount = promotion.discount_value
    return min(discount, subtotal).quantize(Decimal('0.01'))


def get_cart_discount_preview(cart, subtotal):
    if cart.applied_promotion_id is None:
        return None
    promotion = cart.applied_promotion
    try:
        validate_promotion(promotion, subtotal)
    except PromotionError:
        return None
    discount_amount = calculate_discount(promotion, subtotal)
    return {
        'code': promotion.code,
        'discount_amount': discount_amount,
        'total': (subtotal - discount_amount).quantize(Decimal('0.01')),
    }


def apply_promotion_to_cart(cart, code):
    promotion = get_promotion_by_code(code)
    from cart.services import compute_cart_summary
    subtotal = compute_cart_summary(cart)['subtotal']
    validate_promotion(promotion, subtotal)
    cart.applied_promotion = promotion
    cart.save(update_fields=['applied_promotion', 'updated_at'])
    return get_cart_discount_preview(cart, subtotal)


def remove_promotion_from_cart(cart):
    cart.applied_promotion = None
    cart.save(update_fields=['applied_promotion', 'updated_at'])


def resolve_promotion_for_checkout(cart, subtotal):
    if cart.applied_promotion_id is None:
        return '', Decimal('0.00')
    promotion = cart.applied_promotion
    validate_promotion(promotion, subtotal)
    discount_amount = calculate_discount(promotion, subtotal)
    return promotion.code, discount_amount


def increment_promotion_usage(code):
    promotion = Promotion.objects.select_for_update().get(code=code.upper())
    validate_promotion(promotion, Decimal('0.00'))
    if promotion.max_uses is not None and promotion.used_count >= promotion.max_uses:
        raise PromotionError('This promotion has reached its usage limit.')
    promotion.used_count += 1
    promotion.save(update_fields=['used_count', 'updated_at'])
    return promotion
