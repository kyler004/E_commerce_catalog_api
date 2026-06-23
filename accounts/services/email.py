from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string


def send_otp_email(to_email, code, purpose):
    purpose_label = 'verify your account' if purpose == 'signup' else 'reset your password'
    subject = 'Your verification code'
    message = render_to_string(
        'accounts/otp_email.txt',
        {
            'code': code,
            'purpose_label': purpose_label,
            'expiry_minutes': settings.OTP_EXPIRY_MINUTES,
        },
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to_email],
        fail_silently=False,
    )
