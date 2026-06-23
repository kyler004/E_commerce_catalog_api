from api.models import Product
from orders.models import Order, OrderItem
from reviews.models import Review


class ReviewValidationError(Exception):
    pass


def user_has_purchased_product(user, product):
    return OrderItem.objects.filter(
        order__user=user,
        order__status=Order.Status.PAID,
        variant__product=product,
    ).exists()


def get_product_rating_summary(product):
    reviews = Review.objects.filter(product=product)
    count = reviews.count()
    if count == 0:
        return {'average_rating': None, 'review_count': 0}
    average = sum(review.rating for review in reviews) / count
    return {'average_rating': round(average, 2), 'review_count': count}


def create_review(user, product_id, data):
    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist as exc:
        raise ReviewValidationError('Product not found.') from exc

    if not user_has_purchased_product(user, product):
        raise ReviewValidationError('You can only review products you have purchased.')

    if Review.objects.filter(user=user, product=product).exists():
        raise ReviewValidationError('You have already reviewed this product.')

    return Review.objects.create(user=user, product=product, **data)
