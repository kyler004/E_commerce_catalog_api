from api.models import Product, Variant
from cart.services import CartValidationError, add_item
from wishlists.models import Wishlist, WishlistItem


class WishlistValidationError(Exception):
    pass


def get_or_create_wishlist(user):
    wishlist, _ = Wishlist.objects.get_or_create(user=user)
    return wishlist


def add_product(user, product_id):
    wishlist = get_or_create_wishlist(user)
    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist as exc:
        raise WishlistValidationError('Product not found.') from exc

    if WishlistItem.objects.filter(wishlist=wishlist, product=product).exists():
        raise WishlistValidationError('Product is already in the wishlist.')

    return WishlistItem.objects.create(wishlist=wishlist, product=product)


def remove_item(user, item_id):
    wishlist = get_or_create_wishlist(user)
    try:
        item = WishlistItem.objects.get(pk=item_id, wishlist=wishlist)
    except WishlistItem.DoesNotExist as exc:
        raise WishlistItem.DoesNotExist from exc
    item.delete()


def move_to_cart(user, item_id, variant_id, quantity=1):
    wishlist = get_or_create_wishlist(user)
    try:
        item = WishlistItem.objects.select_related('product').get(pk=item_id, wishlist=wishlist)
    except WishlistItem.DoesNotExist as exc:
        raise WishlistItem.DoesNotExist from exc

    try:
        variant = Variant.objects.get(pk=variant_id, product=item.product)
    except Variant.DoesNotExist as exc:
        raise WishlistValidationError('Variant does not belong to this product.') from exc

    try:
        cart_item, _ = add_item(user, variant.id, quantity)
    except CartValidationError as exc:
        raise WishlistValidationError(str(exc)) from exc

    item.delete()
    return cart_item
