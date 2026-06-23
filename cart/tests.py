from decimal import Decimal

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from api.models import Category, Inventory, Product, Variant
from cart.models import Cart, CartItem


class CartFixturesMixin:
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
        self.inventory = Inventory.objects.create(variant=self.variant, quantity=50)

        self.cart_url = '/api/cart/'
        self.items_url = '/api/cart/items/'
        self.client.force_authenticate(user=self.user)


class CartAPITestCase(CartFixturesMixin, APITestCase):
    def test_get_empty_cart(self):
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['items'], [])
        self.assertEqual(data['item_count'], 0)
        self.assertEqual(data['subtotal'], '0.00')

    def test_add_item(self):
        response = self.client.post(
            self.items_url,
            {'variant': self.variant.id, 'quantity': 2},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['quantity'], 2)
        self.assertEqual(response.json()['unit_price'], '79.99')
        self.assertEqual(CartItem.objects.count(), 1)

    def test_add_same_variant_merges_quantity(self):
        self.client.post(
            self.items_url,
            {'variant': self.variant.id, 'quantity': 2},
            format='json',
        )
        self.client.post(
            self.items_url,
            {'variant': self.variant.id, 'quantity': 3},
            format='json',
        )
        self.assertEqual(CartItem.objects.count(), 1)
        item = CartItem.objects.get()
        self.assertEqual(item.quantity, 5)

    def test_add_exceeds_stock_returns_400(self):
        response = self.client.post(
            self.items_url,
            {'variant': self.variant.id, 'quantity': 51},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Insufficient stock', response.json()['detail'])

    def test_update_item_quantity(self):
        add_response = self.client.post(
            self.items_url,
            {'variant': self.variant.id, 'quantity': 2},
            format='json',
        )
        item_id = add_response.json()['id']
        response = self.client.patch(
            f'{self.items_url}{item_id}/',
            {'quantity': 4},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['quantity'], 4)

    def test_remove_item(self):
        add_response = self.client.post(
            self.items_url,
            {'variant': self.variant.id, 'quantity': 1},
            format='json',
        )
        item_id = add_response.json()['id']
        response = self.client.delete(f'{self.items_url}{item_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_clear_cart(self):
        self.client.post(
            self.items_url,
            {'variant': self.variant.id, 'quantity': 2},
            format='json',
        )
        response = self.client.delete(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_subtotal_and_item_count(self):
        self.client.post(
            self.items_url,
            {'variant': self.variant.id, 'quantity': 2},
            format='json',
        )
        response = self.client.get(self.cart_url)
        data = response.json()
        self.assertEqual(data['item_count'], 2)
        self.assertEqual(data['subtotal'], '159.98')

    def test_unauthenticated_returns_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unverified_user_returns_403(self):
        unverified = User.objects.create_user(
            email='unverified@test.com',
            password='TestPass123!',
            is_active=True,
        )
        self.client.force_authenticate(user=unverified)
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_foreign_item_returns_404(self):
        add_response = self.client.post(
            self.items_url,
            {'variant': self.variant.id, 'quantity': 1},
            format='json',
        )
        item_id = add_response.json()['id']
        self.client.force_authenticate(user=self.other_user)
        response = self.client.patch(
            f'{self.items_url}{item_id}/',
            {'quantity': 2},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_or_create_cart_on_first_access(self):
        self.assertFalse(Cart.objects.filter(user=self.user).exists())
        self.client.get(self.cart_url)
        self.assertTrue(Cart.objects.filter(user=self.user).exists())
