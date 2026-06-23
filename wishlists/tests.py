from decimal import Decimal

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from api.models import Category, Inventory, Product, Variant
from cart.models import CartItem
from wishlists.models import WishlistItem


class WishlistAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='shopper@test.com',
            password='TestPass123!',
            is_active=True,
        )
        self.user.email_verified_at = timezone.now()
        self.user.save(update_fields=['email_verified_at'])
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
        self.url = '/api/wishlist/'

    def test_add_and_list_wishlist_item(self):
        response = self.client.post(
            f'{self.url}items/',
            {'product': self.product.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        list_response = self.client.get(self.url)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.json()['item_count'], 1)

    def test_duplicate_product_returns_400(self):
        self.client.post(f'{self.url}items/', {'product': self.product.id}, format='json')
        response = self.client.post(
            f'{self.url}items/',
            {'product': self.product.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_move_to_cart(self):
        add_response = self.client.post(
            f'{self.url}items/',
            {'product': self.product.id},
            format='json',
        )
        item_id = add_response.json()['id']
        response = self.client.post(
            f'{self.url}items/{item_id}/move-to-cart/',
            {'variant': self.variant.id, 'quantity': 2},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CartItem.objects.count(), 1)
        self.assertEqual(WishlistItem.objects.count(), 0)

    def test_unauthenticated_returns_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
