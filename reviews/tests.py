from decimal import Decimal

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from api.models import Category, Inventory, Product, Variant
from cart.services import add_item
from orders.models import Order
from orders.services import checkout, confirm_payment
from reviews.models import Review


class ReviewAPITestCase(APITestCase):
    shipping_payload = {
        'full_name': 'Jane Doe',
        'address_line1': '123 Main St',
        'city': 'Paris',
        'postal_code': '75001',
        'country': 'FR',
    }

    def setUp(self):
        self.user = User.objects.create_user(
            email='shopper@test.com',
            password='TestPass123!',
            is_active=True,
        )
        self.user.email_verified_at = timezone.now()
        self.user.save(update_fields=['email_verified_at'])
        self.other_user = User.objects.create_user(
            email='other@test.com',
            password='TestPass123!',
            is_active=True,
        )
        self.other_user.email_verified_at = timezone.now()
        self.other_user.save(update_fields=['email_verified_at'])

        self.category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            name='Wireless Headphones',
            description='Noise-cancelling headphones',
            price=Decimal('79.99'),
            category=self.category,
        )
        self.variant = Variant.objects.create(
            product=self.product,
            size='L',
            color='Red',
            sku='WH-L-RED',
        )
        Inventory.objects.create(variant=self.variant, quantity=50)
        self.client.force_authenticate(user=self.user)

    def _complete_purchase(self, user=None):
        user = user or self.user
        add_item(user, self.variant.id, 1)
        order = checkout(user, self.shipping_payload)
        confirm_payment(user, order.id)

    def test_create_review_after_purchase(self):
        self._complete_purchase()
        response = self.client.post(
            f'/api/products/{self.product.id}/reviews/',
            {'rating': 5, 'title': 'Great', 'body': 'Love these headphones.'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.count(), 1)

    def test_create_review_without_purchase_returns_400(self):
        response = self.client.post(
            f'/api/products/{self.product.id}/reviews/',
            {'rating': 5, 'title': 'Great', 'body': 'Love these headphones.'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_reviews_is_public(self):
        self._complete_purchase()
        self.client.post(
            f'/api/products/{self.product.id}/reviews/',
            {'rating': 4, 'title': 'Good', 'body': 'Solid product.'},
            format='json',
        )
        self.client.force_authenticate(user=None)
        response = self.client.get(f'/api/products/{self.product.id}/reviews/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 1)

    def test_product_includes_rating_summary(self):
        self._complete_purchase()
        self.client.post(
            f'/api/products/{self.product.id}/reviews/',
            {'rating': 4, 'title': 'Good', 'body': 'Solid product.'},
            format='json',
        )
        response = self.client.get(f'/api/products/{self.product.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['review_count'], 1)
        self.assertEqual(float(response.json()['average_rating']), 4.0)

    def test_cannot_edit_other_users_review(self):
        self._complete_purchase()
        review_id = self.client.post(
            f'/api/products/{self.product.id}/reviews/',
            {'rating': 4, 'title': 'Good', 'body': 'Solid product.'},
            format='json',
        ).json()['id']
        self.client.force_authenticate(user=self.other_user)
        response = self.client.patch(
            f'/api/reviews/{review_id}/',
            {'rating': 1},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
