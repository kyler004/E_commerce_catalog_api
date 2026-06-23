import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone

from accounts.models import EmailOTP, User


class OTPError(Exception):
    pass


class OTPRateLimitError(OTPError):
    pass


class OTPValidationError(OTPError):
    pass


def _generate_code():
    upper = 10 ** settings.OTP_LENGTH
    return str(secrets.randbelow(upper)).zfill(settings.OTP_LENGTH)


def _get_latest_otp(user, purpose):
    return (
        EmailOTP.objects.filter(user=user, purpose=purpose)
        .order_by('-created_at')
        .first()
    )


def create_otp(user, purpose):
    latest = _get_latest_otp(user, purpose)
    if latest and not latest.is_used:
        elapsed = (timezone.now() - latest.created_at).total_seconds()
        if elapsed < settings.OTP_RESEND_COOLDOWN_SECONDS:
            raise OTPRateLimitError(
                'Please wait before requesting another code.'
            )

    EmailOTP.objects.filter(
        user=user,
        purpose=purpose,
        is_used=False,
    ).update(is_used=True)

    code = _generate_code()
    otp = EmailOTP.objects.create(
        user=user,
        purpose=purpose,
        code_hash=make_password(code),
        expires_at=timezone.now() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES),
    )
    return code, otp


def verify_otp(user, purpose, code):
    otp = (
        EmailOTP.objects.filter(
            user=user,
            purpose=purpose,
            is_used=False,
        )
        .order_by('-created_at')
        .first()
    )
    if otp is None:
        raise OTPValidationError('Invalid or expired code.')

    if timezone.now() > otp.expires_at:
        raise OTPValidationError('Invalid or expired code.')

    if otp.attempts >= settings.OTP_MAX_ATTEMPTS:
        raise OTPValidationError('Invalid or expired code.')

    if not check_password(code, otp.code_hash):
        otp.attempts += 1
        otp.save(update_fields=['attempts'])
        raise OTPValidationError('Invalid or expired code.')

    otp.is_used = True
    otp.save(update_fields=['is_used'])
    return otp


def get_user_by_email(email):
    return User.objects.filter(email__iexact=email).first()
