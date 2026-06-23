from django.urls import path

from accounts.views import (
    CustomTokenObtainPairView,
    ForgotPasswordView,
    MeView,
    RegisterView,
    ResendOTPView,
    ResetPasswordView,
    TokenRefreshAPIView,
    VerifyEmailView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth-register'),
    path('verify-email/', VerifyEmailView.as_view(), name='auth-verify-email'),
    path('resend-otp/', ResendOTPView.as_view(), name='auth-resend-otp'),
    path('login/', CustomTokenObtainPairView.as_view(), name='auth-login'),
    path('token/refresh/', TokenRefreshAPIView.as_view(), name='auth-token-refresh'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='auth-forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='auth-reset-password'),
    path('me/', MeView.as_view(), name='auth-me'),
]
