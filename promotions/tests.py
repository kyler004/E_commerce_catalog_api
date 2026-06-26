from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from api.models import Category, Inventory, Product, Variant
from cart.services import add_item
from orders.models import Order
from promotions.models import Promotion


class PromotionFixturesMixin:
    shipping_payload = {
        'full_name': 'Jane Doe',
        'address_line1': '123 Main St',
        'city': 'Paris',
        'postal_code': '75001',
        'country': 'FR',
    }

    def setUp(self):
        self.client = APITestCase.client_class()
        self.user = User.objects.create_user(
            email='shopper@test.com',
            password='TestPass123!',
            is_active=True,
        )
        self.user.email_verified_at = timezone.now()
        self.user.save(update_fields=['email_verified_at'])
        self.staff = User.objects.create_user(
            email='staff@test.com',
            password='TestPass123!',
            is_active=True,
            is_staff=True,
        )
        self.staff.email_verified_at = timezone.now()
        self.staff.save(update_fields=['email_verified_at'])

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
        self.promotion = Promotion.objects.create(
            code='SAVE10',
            discount_type=Promotion.DiscountType.PERCENTAGE,
            discount_value=Decimal('10'),
            is_active=True,
        )
        self.client.force_authenticate(user=self.user)


class PromotionAPITestCase(PromotionFixturesMixin, APITestCase):
    def test_staff_can_create_promotion(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.post(
            '/api/promotions/',
            {
                'code': 'FIXED5',
                'discount_type': 'fixed',
                'discount_value': '5.00',
                'is_active': True,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_non_staff_cannot_create_promotion(self):
        response = self.client.post(
            '/api/promotions/',
            {
                'code': 'NOPE',
                'discount_type': 'fixed',
                'discount_value': '5.00',
                'is_active': True,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unverified_staff_cannot_create_promotion(self):
        unverified_staff = User.objects.create_user(
            email='unverified-staff@test.com',
            password='TestPass123!',
            is_active=True,
            is_staff=True,
        )
        self.client.force_authenticate(user=unverified_staff)
        response = self.client.post(
            '/api/promotions/',
            {
                'code': 'NOPE',
                'discount_type': 'fixed',
                'discount_value': '5.00',
                'is_active': True,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_apply_promo_to_cart(self):
        add_item(self.user, self.variant.id, 2)
        response = self.client.post(
            '/api/cart/apply-promo/',
            {'code': 'SAVE10'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['promotion']['code'], 'SAVE10')

    def test_apply_inactive_promo_returns_400(self):
        self.promotion.is_active = False
        self.promotion.save(update_fields=['is_active'])
        add_item(self.user, self.variant.id, 1)
        response = self.client.post(
            '/api/cart/apply-promo/',
            {'code': 'SAVE10'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['detail'], 'This promotion is not active.')

    def test_apply_expired_promo_returns_400(self):
        self.promotion.valid_until = timezone.now() - timedelta(days=1)
        self.promotion.save(update_fields=['valid_until'])
        add_item(self.user, self.variant.id, 1)
        response = self.client.post(
            '/api/cart/apply-promo/',
            {'code': 'SAVE10'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['detail'], 'This promotion is not currently valid.')

    def test_apply_promo_below_minimum_returns_400(self):
        self.promotion.min_order_amount = Decimal('100.00')
        self.promotion.save(update_fields=['min_order_amount'])
        add_item(self.user, self.variant.id, 1)
        response = self.client.post(
            '/api/cart/apply-promo/',
            {'code': 'SAVE10'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Minimum order amount', response.json()['detail'])

    def test_apply_promo_at_usage_limit_returns_400(self):
        self.promotion.max_uses = 1
        self.promotion.used_count = 1
        self.promotion.save(update_fields=['max_uses', 'used_count'])
        add_item(self.user, self.variant.id, 1)
        response = self.client.post(
            '/api/cart/apply-promo/',
            {'code': 'SAVE10'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['detail'], 'This promotion has reached its usage limit.')

    def test_checkout_applies_discount(self):
        add_item(self.user, self.variant.id, 2)
        self.client.post('/api/cart/apply-promo/', {'code': 'SAVE10'}, format='json')
        response = self.client.post(
            '/api/orders/checkout/',
            {'shipping': self.shipping_payload},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data['promotion_code'], 'SAVE10')
        self.assertEqual(data['discount_amount'], '16.00')
        self.assertEqual(data['total'], '143.98')

    def test_fixed_discount_is_capped_at_subtotal(self):
        capped = Promotion.objects.create(
            code='FREE',
            discount_type=Promotion.DiscountType.FIXED,
            discount_value=Decimal('500.00'),
            is_active=True,
        )
        add_item(self.user, self.variant.id, 1)
        self.client.post('/api/cart/apply-promo/', {'code': capped.code}, format='json')
        response = self.client.post(
            '/api/orders/checkout/',
            {'shipping': self.shipping_payload},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['discount_amount'], '79.99')
        self.assertEqual(response.json()['total'], '0.00')

    def test_used_count_increments_on_payment(self):
        add_item(self.user, self.variant.id, 1)
        self.client.post('/api/cart/apply-promo/', {'code': 'SAVE10'}, format='json')
        order_id = self.client.post(
            '/api/orders/checkout/',
            {'shipping': self.shipping_payload},
            format='json',
        ).json()['id']
        self.client.post(f'/api/orders/{order_id}/confirm-payment/')
        self.promotion.refresh_from_db()
        self.assertEqual(self.promotion.used_count, 1)

    def test_remove_promo_from_cart(self):
        add_item(self.user, self.variant.id, 1)
        self.client.post('/api/cart/apply-promo/', {'code': 'SAVE10'}, format='json')
        response = self.client.delete('/api/cart/promo/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.json()['promotion'])
