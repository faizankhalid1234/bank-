"""Send email OTP for registration via Django mail (SMTP or console in dev)."""

import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def _email_otp_body(otp: str) -> str:
    return (
        f"AlyBank email verification code: {otp}\n\n"
        "Valid for 10 minutes. Do not share this code with anyone.\n\n"
        "If you did not request this, ignore this message."
    )


def send_registration_email_otp(to_email: str, otp: str) -> tuple[bool, str, str | None]:
    """
    Send OTP to the user's email (real inbox — Gmail app on phone included).

    Returns (success_flag, message_key, otp_for_json_or_none).

    message_key: 'email_sent' | 'email_failed' | 'email_demo'

    In DEBUG, on send failure we return email_demo + OTP so the SPA can show it (like SMS demo).
    """
    to_email = (to_email or "").strip()
    if not to_email:
        return False, "email_failed", None

    subject = "AlyBank — email verification code"
    body = _email_otp_body(otp)
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or getattr(
        settings, "EMAIL_HOST_USER", ""
    ) or "noreply@localhost"

    try:
        send_mail(
            subject,
            body,
            from_email,
            [to_email],
            fail_silently=False,
        )
        logger.info("Registration email OTP sent to %s", to_email)
        return True, "email_sent", None
    except Exception:
        logger.exception("Registration email OTP failed for %s", to_email)
        if getattr(settings, "DEBUG", False):
            return True, "email_demo", otp
        return False, "email_failed", None
