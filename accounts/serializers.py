from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from accounts.models import EmailOTP, User
from accounts.services.otp import (
    OTPRateLimitError,
    OTPValidationError,
    create_otp,
    get_user_by_email,
    verify_otp,
)


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value.lower()

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            is_active=False,
        )
        return user


class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(min_length=6, max_length=6)

    def validate(self, attrs):
        user = get_user_by_email(attrs['email'])
        if user is None:
            raise serializers.ValidationError({'otp': 'Invalid or expired code.'})
        try:
            verify_otp(user, EmailOTP.Purpose.SIGNUP, attrs['otp'])
        except OTPValidationError:
            raise serializers.ValidationError({'otp': 'Invalid or expired code.'}) from None
        attrs['user'] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data['user']
        user.is_active = True
        user.email_verified_at = timezone.now()
        user.save(update_fields=['is_active', 'email_verified_at'])
        return user


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    purpose = serializers.ChoiceField(choices=EmailOTP.Purpose.choices)

    def validate(self, attrs):
        user = get_user_by_email(attrs['email'])
        if user is None:
            raise serializers.ValidationError({'email': 'User not found.'})

        purpose = attrs['purpose']
        if purpose == EmailOTP.Purpose.SIGNUP and user.is_email_verified:
            raise serializers.ValidationError({'email': 'Email is already verified.'})
        if purpose == EmailOTP.Purpose.PASSWORD_RESET and not user.is_email_verified:
            raise serializers.ValidationError({'email': 'Account is not verified.'})

        attrs['user'] = user
        return attrs


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(min_length=6, max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        user = get_user_by_email(attrs['email'])
        if user is None:
            raise serializers.ValidationError({'otp': 'Invalid or expired code.'})
        try:
            verify_otp(user, EmailOTP.Purpose.PASSWORD_RESET, attrs['otp'])
        except OTPValidationError:
            raise serializers.ValidationError({'otp': 'Invalid or expired code.'}) from None
        attrs['user'] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'email_verified_at']


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = User.USERNAME_FIELD

    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.is_email_verified:
            raise serializers.ValidationError(
                {'detail': 'No active account found with the given credentials.'}
            )
        return data
