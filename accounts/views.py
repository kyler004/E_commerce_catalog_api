from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts.models import EmailOTP
from accounts.serializers import (
    CustomTokenObtainPairSerializer,
    ForgotPasswordSerializer,
    RegisterSerializer,
    ResendOTPSerializer,
    ResetPasswordSerializer,
    UserProfileSerializer,
    VerifyEmailSerializer,
)
from accounts.services.email import send_otp_email
from accounts.services.otp import OTPRateLimitError, create_otp, get_user_by_email


class OTPRateThrottle(SimpleRateThrottle):
    scope = 'otp'

    def get_cache_key(self, request, view):
        email = request.data.get('email', '')
        return self.cache_format % {'scope': self.scope, 'ident': email.lower()}


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OTPRateThrottle]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        try:
            code, _ = create_otp(user, EmailOTP.Purpose.SIGNUP)
        except OTPRateLimitError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        send_otp_email(user.email, code, EmailOTP.Purpose.SIGNUP)
        return Response(
            {'detail': 'Verification code sent to your email.'},
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Email verified successfully.'})


class ResendOTPView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OTPRateThrottle]

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        purpose = serializer.validated_data['purpose']
        try:
            code, _ = create_otp(user, purpose)
        except OTPRateLimitError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        send_otp_email(user.email, code, purpose)
        return Response({'detail': 'Verification code sent to your email.'})


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        if email:
            user = get_user_by_email(email)
            if user is None or not user.is_active or not user.is_email_verified:
                return Response(
                    {'detail': 'No active account found with the given credentials.'},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
        return super().post(request, *args, **kwargs)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OTPRateThrottle]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_user_by_email(serializer.validated_data['email'])
        if user is not None and user.is_email_verified:
            try:
                code, _ = create_otp(user, EmailOTP.Purpose.PASSWORD_RESET)
                send_otp_email(user.email, code, EmailOTP.Purpose.PASSWORD_RESET)
            except OTPRateLimitError:
                pass
        return Response(
            {'detail': 'If an account exists for this email, a verification code has been sent.'},
        )


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Password reset successfully.'})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)


class TokenRefreshAPIView(TokenRefreshView):
    permission_classes = [AllowAny]
