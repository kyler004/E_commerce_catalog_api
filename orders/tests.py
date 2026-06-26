from decimal import Decimal
from datetime import timedelta, timezone as datetime_timezone

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from api.models import Category, Inventory, Product, Variant
from cart.models import CartItem
from cart.services import add_item
from orders.models import Order, OrderItem


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

    def _paid_order(self, user=None, quantity=1, paid_at=None):
        self._add_to_cart(user=user, quantity=quantity)
        order_id = self._checkout(user=user).json()['id']
        self.client.post(f'{self.orders_url}{order_id}/confirm-payment/')
        if paid_at is not None:
            Order.objects.filter(pk=order_id).update(paid_at=paid_at)
        return Order.objects.get(pk=order_id)


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
        self.assertEqual(data['items'][0]['category_id'], self.category.id)
        self.assertEqual(data['items'][0]['category_name'], 'Electronics')
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

    def test_list_orders_filters_by_status_and_date_range(self):
        order_2026 = self._paid_order(
            paid_at=timezone.datetime(2026, 6, 15, tzinfo=datetime_timezone.utc),
        )
        self._paid_order(
            paid_at=timezone.datetime(2025, 6, 15, tzinfo=datetime_timezone.utc),
        )
        self._add_to_cart(quantity=1)
        self._checkout()

        response = self.client.get(
            self.orders_url,
            {
                'status': 'paid',
                'paid_after': '2026-01-01',
                'paid_before': '2026-12-31',
                'ordering': '-paid_at',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 1)
        self.assertEqual(response.json()['results'][0]['id'], order_2026.id)

    def test_list_orders_filters_by_created_date_range(self):
        first_order = self._paid_order()
        second_order = self._paid_order()
        Order.objects.filter(pk=first_order.id).update(
            created_at=timezone.datetime(2026, 1, 15, tzinfo=datetime_timezone.utc),
        )
        Order.objects.filter(pk=second_order.id).update(
            created_at=timezone.datetime(2026, 3, 15, tzinfo=datetime_timezone.utc),
        )

        response = self.client.get(
            self.orders_url,
            {
                'created_after': '2026-03-01',
                'created_before': '2026-03-31',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 1)
        self.assertEqual(response.json()['results'][0]['id'], second_order.id)

    def test_list_orders_rejects_invalid_date_filter(self):
        response = self.client.get(self.orders_url, {'paid_after': 'not-a-date'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_orders_rejects_unsupported_ordering(self):
        response = self.client.get(self.orders_url, {'ordering': 'total'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

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


class SpendingSummaryTestCase(OrderFixturesMixin, APITestCase):
    summary_url = '/api/account/spending-summary/'

    def _create_order(
        self,
        *,
        user=None,
        status_value=Order.Status.PAID,
        total='100.00',
        discount_amount='0.00',
        paid_at=None,
        category=None,
        quantity=1,
    ):
        user = user or self.user
        category = category or self.category
        paid_at = paid_at or timezone.datetime(2026, 6, 15, tzinfo=datetime_timezone.utc)
        order = Order.objects.create(
            user=user,
            status=status_value,
            subtotal=Decimal(total) + Decimal(discount_amount),
            discount_amount=Decimal(discount_amount),
            total=Decimal(total),
            paid_at=paid_at if status_value == Order.Status.PAID else None,
        )
        OrderItem.objects.create(
            order=order,
            variant=self.variant,
            product_name=self.product.name,
            sku=self.variant.sku,
            size=self.variant.size,
            color=self.variant.color,
            category_id=category.id,
            category_name=category.name,
            quantity=quantity,
            unit_price=Decimal(total),
            line_total=Decimal(total),
        )
        return order

    def test_spending_summary_aggregates_paid_orders_only(self):
        apparel = Category.objects.create(name='Apparel')
        self._create_order(
            total='100.00',
            discount_amount='10.00',
            paid_at=timezone.datetime(2026, 6, 15, tzinfo=datetime_timezone.utc),
            category=apparel,
            quantity=2,
        )
        self._create_order(
            total='200.00',
            discount_amount='20.00',
            paid_at=timezone.datetime(2026, 7, 15, tzinfo=datetime_timezone.utc),
        )
        self._create_order(status_value=Order.Status.PENDING, total='999.00')
        self._create_order(status_value=Order.Status.CANCELLED, total='999.00')
        self._create_order(user=self.other_user, total='500.00')

        response = self.client.get(self.summary_url, {'period': 'all'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['currency'], 'USD')
        self.assertEqual(data['lifetime_spend'], '300.00')
        self.assertEqual(data['paid_order_count'], 2)
        self.assertEqual(data['pending_order_count'], 1)
        self.assertEqual(data['cancelled_order_count'], 1)
        self.assertEqual(data['total_savings'], '30.00')
        self.assertEqual(data['average_order_value'], '150.00')
        self.assertEqual(
            data['spending_by_month'],
            [
                {'period': '2026-06', 'total': '100.00', 'order_count': 1},
                {'period': '2026-07', 'total': '200.00', 'order_count': 1},
            ],
        )
        self.assertEqual(data['spending_by_category'][0]['category_name'], 'Electronics')
        self.assertEqual(data['spending_by_category'][0]['total'], '200.00')
        self.assertEqual(data['recent_paid_orders'][0]['item_count'], 1)

    def test_spending_summary_requires_verified_user(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.summary_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        unverified = User.objects.create_user(
            email='summary-unverified@test.com',
            password='TestPass123!',
            is_active=True,
        )
        self.client.force_authenticate(user=unverified)
        response = self.client.get(self.summary_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_spending_summary_rejects_invalid_period(self):
        response = self.client.get(self.summary_url, {'period': 'year'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_spending_summary_period_limits_chart_aggregates_only(self):
        recent_paid_at = timezone.now()
        old_paid_at = recent_paid_at - timedelta(days=400)
        self._create_order(total='50.00', paid_at=old_paid_at)
        self._create_order(total='100.00', paid_at=recent_paid_at)

        response = self.client.get(self.summary_url, {'period': '12m'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['lifetime_spend'], '150.00')
        self.assertEqual(data['paid_order_count'], 2)
        self.assertEqual(len(data['spending_by_month']), 1)
        self.assertEqual(data['spending_by_month'][0]['total'], '100.00')
        self.assertEqual(data['spending_by_category'][0]['total'], '100.00')

    def test_spending_summary_uses_created_at_fallback_for_missing_paid_at(self):
        order = self._create_order(total='75.00')
        Order.objects.filter(pk=order.pk).update(paid_at=None)

        response = self.client.get(self.summary_url, {'period': 'all'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['lifetime_spend'], '75.00')
        self.assertIsNotNone(data['recent_paid_orders'][0]['paid_at'])


class OrderReceiptTestCase(OrderFixturesMixin, APITestCase):
    def test_receipt_for_paid_order_returns_html(self):
        self._add_to_cart()
        order_id = self._checkout().json()['id']
        self.client.post(f'{self.orders_url}{order_id}/confirm-payment/')

        response = self.client.get(f'{self.orders_url}{order_id}/receipt/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/html')
        
        # Verify receipt contents
        html = response.content.decode('utf-8')
        self.assertIn('Receipt for Order #', html)
        self.assertIn(f'Order ID: <strong>#{order_id}</strong>', html)
        self.assertIn('Wireless Headphones', html)
        self.assertIn('WH-L-RED', html)
        self.assertIn('Jane Doe', html)
        self.assertIn('Paris', html)
        self.assertIn('$159.98', html)

    def test_receipt_for_pending_order_returns_400(self):
        self._add_to_cart()
        order_id = self._checkout().json()['id']

        response = self.client.get(f'{self.orders_url}{order_id}/receipt/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['detail'], 'Receipts are only available for paid orders.')

    def test_receipt_for_cancelled_order_returns_400(self):
        self._add_to_cart()
        order_id = self._checkout().json()['id']
        self.client.post(f'{self.orders_url}{order_id}/cancel/')

        response = self.client.get(f'{self.orders_url}{order_id}/receipt/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['detail'], 'Receipts are only available for paid orders.')

    def test_receipt_for_other_users_order_returns_404(self):
        self._add_to_cart()
        order_id = self._checkout().json()['id']
        self.client.post(f'{self.orders_url}{order_id}/confirm-payment/')

        # Authenticate as other user
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(f'{self.orders_url}{order_id}/receipt/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_receipt_unauthenticated_returns_401(self):
        self._add_to_cart()
        order_id = self._checkout().json()['id']
        self.client.post(f'{self.orders_url}{order_id}/confirm-payment/')

        # Logout
        self.client.force_authenticate(user=None)
        response = self.client.get(f'{self.orders_url}{order_id}/receipt/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_receipt_unverified_returns_403(self):
        self._add_to_cart()
        order_id = self._checkout().json()['id']
        self.client.post(f'{self.orders_url}{order_id}/confirm-payment/')

        unverified = User.objects.create_user(
            email='unverified@test.com',
            password='TestPass123!',
            is_active=True,
        )
        self.client.force_authenticate(user=unverified)
        response = self.client.get(f'{self.orders_url}{order_id}/receipt/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_receipt_nonexistent_order_returns_404(self):
        response = self.client.get(f'{self.orders_url}99999/receipt/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
