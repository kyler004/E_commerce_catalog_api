from decimal import Decimal

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from api.models import Category, Inventory, Product, Variant
from cart.models import CartItem
from cart.services import add_item
from orders.models import Order


class OrderFixturesMixin:
    shipping_payload = {
        'full_name': 'Jane Doe',
        'address_line1': '123 Main St',
        'address_line2': 'Apt 4',
        'city': 'Paris',
        'postal_code': '75001',
        'country': 'FR',
        'phone': '+33600000000',
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
        self.inventory = Inventory.objects.create(variant=self.variant, quantity=50)

        self.checkout_url = '/api/orders/checkout/'
        self.orders_url = '/api/orders/'
        self.client.force_authenticate(user=self.user)

    def _add_to_cart(self, user=None, quantity=2):
        user = user or self.user
        add_item(user, self.variant.id, quantity)

    def _checkout(self, user=None):
        user = user or self.user
        self.client.force_authenticate(user=user)
        return self.client.post(
            self.checkout_url,
            {'shipping': self.shipping_payload},
            format='json',
        )


class OrderAPITestCase(OrderFixturesMixin, APITestCase):
    def test_checkout_creates_pending_order(self):
        self._add_to_cart()
        response = self._checkout()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data['status'], 'pending')
        self.assertEqual(data['subtotal'], '159.98')
        self.assertEqual(len(data['items']), 1)
        self.assertEqual(data['items'][0]['sku'], 'WH-L-RED')
        self.assertEqual(data['shipping']['city'], 'Paris')
        self.assertIsNone(data['paid_at'])
        self.assertEqual(CartItem.objects.count(), 0)

    def test_checkout_empty_cart_returns_400(self):
        response = self._checkout()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)

    def test_checkout_requires_shipping(self):
        self._add_to_cart()
        response = self.client.post(self.checkout_url, {'shipping': {}}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkout_validates_stock(self):
        self._add_to_cart(quantity=2)
        self.inventory.quantity = 1
        self.inventory.save(update_fields=['quantity'])
        response = self._checkout()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(CartItem.objects.count(), 1)

    def test_confirm_payment_decrements_inventory(self):
        self._add_to_cart(quantity=2)
        checkout_response = self._checkout()
        order_id = checkout_response.json()['id']

        response = self.client.post(f'{self.orders_url}{order_id}/confirm-payment/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['status'], 'paid')
        self.assertIsNotNone(data['paid_at'])

        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity, 48)

    def test_confirm_payment_revalidates_stock(self):
        self.inventory.quantity = 2
        self.inventory.save()

        self._add_to_cart(quantity=2)
        first_order = self._checkout().json()['id']

        self._add_to_cart(quantity=2)
        second_order = self._checkout().json()['id']

        first_response = self.client.post(f'{self.orders_url}{first_order}/confirm-payment/')
        self.assertEqual(first_response.status_code, status.HTTP_200_OK)

        second_response = self.client.post(f'{self.orders_url}{second_order}/confirm-payment/')
        self.assertEqual(second_response.status_code, status.HTTP_400_BAD_REQUEST)

        order = Order.objects.get(pk=second_order)
        self.assertEqual(order.status, Order.Status.PENDING)

    def test_confirm_payment_non_pending_returns_400(self):
        self._add_to_cart()
        order_id = self._checkout().json()['id']
        self.client.post(f'{self.orders_url}{order_id}/confirm-payment/')

        response = self.client.post(f'{self.orders_url}{order_id}/confirm-payment/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cancel_pending_order(self):
        self._add_to_cart()
        order_id = self._checkout().json()['id']
        initial_stock = self.inventory.quantity

        response = self.client.post(f'{self.orders_url}{order_id}/cancel/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['status'], 'cancelled')

        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity, initial_stock)

    def test_cancel_paid_order_returns_400(self):
        self._add_to_cart()
        order_id = self._checkout().json()['id']
        self.client.post(f'{self.orders_url}{order_id}/confirm-payment/')

        response = self.client.post(f'{self.orders_url}{order_id}/cancel/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_and_retrieve_own_orders(self):
        self._add_to_cart()
        order_id = self._checkout().json()['id']

        list_response = self.client.get(self.orders_url)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.json()['count'], 1)

        detail_response = self.client.get(f'{self.orders_url}{order_id}/')
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.json()['id'], order_id)

    def test_retrieve_other_users_order_returns_404(self):
        self._add_to_cart()
        order_id = self._checkout().json()['id']

        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(f'{self.orders_url}{order_id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_returns_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.orders_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unverified_returns_403(self):
        unverified = User.objects.create_user(
            email='unverified@test.com',
            password='TestPass123!',
            is_active=True,
        )
        self.client.force_authenticate(user=unverified)
        response = self.client.get(self.orders_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_subtotal_and_item_count_on_checkout(self):
        self._add_to_cart(quantity=3)
        response = self._checkout()
        self.assertEqual(response.json()['total'], '239.97')
