from unittest.mock import patch

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import EmailOTP, User


class AuthAPITestCase(APITestCase):
    register_url = '/api/auth/register/'
    verify_url = '/api/auth/verify-email/'
    resend_url = '/api/auth/resend-otp/'
    login_url = '/api/auth/login/'
    forgot_url = '/api/auth/forgot-password/'
    reset_url = '/api/auth/reset-password/'
    me_url = '/api/auth/me/'

    def setUp(self):
        self.email = f'{self._testMethodName}@example.com'
        self.password = 'SecurePass123!'

    @patch('accounts.views.send_otp_email')
    @patch('accounts.services.otp._generate_code', return_value='123456')
    def test_register_creates_inactive_user_and_sends_otp(self, _mock_code, mock_send):
        response = self.client.post(
            self.register_url,
            {'email': self.email, 'password': self.password},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email=self.email)
        self.assertFalse(user.is_active)
        self.assertIsNone(user.email_verified_at)
        mock_send.assert_called_once_with(self.email, '123456', EmailOTP.Purpose.SIGNUP)

    @patch('accounts.views.send_otp_email')
    @patch('accounts.services.otp._generate_code', return_value='123456')
    def test_register_duplicate_email_returns_400(self, _mock_code, _mock_send):
        self.client.post(
            self.register_url,
            {'email': self.email, 'password': self.password},
            format='json',
        )
        response = self.client.post(
            self.register_url,
            {'email': self.email.upper(), 'password': self.password},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('accounts.views.send_otp_email')
    @patch('accounts.services.otp._generate_code', return_value='123456')
    def test_verify_email_activates_user(self, _mock_code, _mock_send):
        self.client.post(
            self.register_url,
            {'email': self.email, 'password': self.password},
            format='json',
        )
        response = self.client.post(
            self.verify_url,
            {'email': self.email, 'otp': '123456'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = User.objects.get(email=self.email)
        self.assertTrue(user.is_active)
        self.assertIsNotNone(user.email_verified_at)

    @patch('accounts.views.send_otp_email')
    @patch('accounts.services.otp._generate_code', return_value='123456')
    def test_verify_rejects_wrong_otp(self, _mock_code, _mock_send):
        self.client.post(
            self.register_url,
            {'email': self.email, 'password': self.password},
            format='json',
        )
        response = self.client.post(
            self.verify_url,
            {'email': self.email, 'otp': '000000'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('accounts.views.send_otp_email')
    @patch('accounts.services.otp._generate_code', return_value='123456')
    def test_login_before_verification_fails(self, _mock_code, _mock_send):
        self.client.post(
            self.register_url,
            {'email': self.email, 'password': self.password},
            format='json',
        )
        response = self.client.post(
            self.login_url,
            {'email': self.email, 'password': self.password},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('accounts.views.send_otp_email')
    @patch('accounts.services.otp._generate_code', return_value='123456')
    def test_login_after_verification_returns_tokens(self, _mock_code, _mock_send):
        self.client.post(
            self.register_url,
            {'email': self.email, 'password': self.password},
            format='json',
        )
        self.client.post(
            self.verify_url,
            {'email': self.email, 'otp': '123456'},
            format='json',
        )
        response = self.client.post(
            self.login_url,
            {'email': self.email, 'password': self.password},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.json())
        self.assertIn('refresh', response.json())

    @patch('accounts.views.send_otp_email')
    @patch('accounts.services.otp._generate_code', return_value='123456')
    def test_forgot_and_reset_password(self, _mock_code, mock_send):
        self._create_verified_user()
        new_password = 'NewSecurePass456!'

        forgot_response = self.client.post(
            self.forgot_url,
            {'email': self.email},
            format='json',
        )
        self.assertEqual(forgot_response.status_code, status.HTTP_200_OK)
        mock_send.assert_called()

        reset_response = self.client.post(
            self.reset_url,
            {'email': self.email, 'otp': '123456', 'new_password': new_password},
            format='json',
        )
        self.assertEqual(reset_response.status_code, status.HTTP_200_OK)

        login_response = self.client.post(
            self.login_url,
            {'email': self.email, 'password': new_password},
            format='json',
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

    @patch('accounts.views.send_otp_email')
    def test_forgot_password_for_unknown_email_does_not_send(self, mock_send):
        response = self.client.post(
            self.forgot_url,
            {'email': 'missing@example.com'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_send.assert_not_called()

    @patch('accounts.views.send_otp_email')
    @patch('accounts.services.otp._generate_code', return_value='123456')
    def test_reset_password_rejects_wrong_otp(self, _mock_code, _mock_send):
        self._create_verified_user()
        self.client.post(self.forgot_url, {'email': self.email}, format='json')
        response = self.client.post(
            self.reset_url,
            {'email': self.email, 'otp': '000000', 'new_password': 'NewSecurePass456!'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('accounts.views.send_otp_email')
    @patch('accounts.services.otp._generate_code', return_value='123456')
    def test_resend_otp_enforces_cooldown(self, _mock_code, _mock_send):
        self.client.post(
            self.register_url,
            {'email': self.email, 'password': self.password},
            format='json',
        )
        response = self.client.post(
            self.resend_url,
            {'email': self.email, 'purpose': EmailOTP.Purpose.SIGNUP},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_resend_signup_otp_for_verified_user_returns_400(self):
        self._create_verified_user()
        response = self.client.post(
            self.resend_url,
            {'email': self.email, 'purpose': EmailOTP.Purpose.SIGNUP},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_resend_password_reset_for_unverified_user_returns_400(self):
        User.objects.create_user(
            email=self.email,
            password=self.password,
            is_active=False,
        )
        response = self.client.post(
            self.resend_url,
            {'email': self.email, 'purpose': EmailOTP.Purpose.PASSWORD_RESET},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('accounts.views.send_otp_email')
    @patch('accounts.services.otp._generate_code', return_value='123456')
    def test_me_requires_authentication(self, _mock_code, _mock_send):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        user = self._create_verified_user()
        self.client.force_authenticate(user=user)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['email'], self.email)

    def _create_verified_user(self):
        user = User.objects.create_user(
            email=self.email,
            password=self.password,
            is_active=True,
        )
        user.email_verified_at = timezone.now()
        user.save(update_fields=['email_verified_at'])
        return user
