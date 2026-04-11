"""Send registration OTP email (HTML + plain text). Works with Brevo SMTP and other providers."""

from __future__ import annotations

import html
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)


def _smtp_credentials_set() -> bool:
    u = (getattr(settings, "EMAIL_HOST_USER", None) or "").strip()
    p = (getattr(settings, "EMAIL_HOST_PASSWORD", None) or "").strip()
    return bool(u and p)


def transactional_from_email() -> str:
    """From header for OTP mail — never use *@smtp-brevo.com as visible sender."""
    from_email = (getattr(settings, "DEFAULT_FROM_EMAIL", None) or "").strip()
    if not from_email:
        u = (getattr(settings, "EMAIL_HOST_USER", None) or "").strip()
        if u and "@smtp-brevo.com" not in u.lower():
            from_email = f"AlyBank <{u}>" if "<" not in u else u
    return from_email


def _otp_digits_row(otp: str) -> str:
    cells = []
    for ch in otp:
        c = html.escape(ch)
        cells.append(
            '<td style="padding:0 4px;">'
            f'<div style="display:inline-block;min-width:40px;padding:14px 10px;text-align:center;'
            f"background:#ffffff;border:2px solid #99f6e4;border-radius:14px;"
            f"font-size:22px;font-weight:700;color:#0f766e;font-family:Georgia,'Times New Roman',serif;"
            f'box-shadow:0 4px 20px rgba(45,212,191,0.15);">{c}</div>'
            "</td>"
        )
    return "".join(cells)


def build_registration_otp_email(otp: str) -> tuple[str, str, str]:
    """
    Returns (subject, plain_text, html_body).
    """
    subject = "AlyBank — your verification code (almost there!)"
    plain = (
        f"Hi from AlyBank 💚\n\n"
        f"Your email verification code is: {otp}\n\n"
        "It's valid for 10 minutes — just for you. Please don't share it with anyone.\n\n"
        "If you weren't signing up, you can ignore this email and we'll leave you in peace.\n"
    )

    digits_row = _otp_digits_row(otp)
    bank_name = html.escape(getattr(settings, "BANK_NAME_EMAIL", "AlyBank"))

    html_body = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="color-scheme" content="light">
  <meta name="supported-color-schemes" content="light">
</head>
<body style="margin:0;padding:0;background:#fdf2f8;font-family:Georgia,'Palatino Linotype',Palatino,serif;">
  <!-- soft outer glow -->
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:linear-gradient(180deg,#fdf2f8 0%,#ecfeff 45%,#f0fdfa 100%);padding:40px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:560px;background:#ffffff;border-radius:24px;overflow:hidden;box-shadow:0 4px 6px rgba(15,23,42,0.04),0 24px 48px rgba(13,148,136,0.12);border:1px solid rgba(153,246,228,0.6);">
          <!-- header -->
          <tr>
            <td style="background:linear-gradient(125deg,#14b8a6 0%,#0d9488 35%,#0f766e 70%,#115e59 100%);padding:36px 28px 32px;text-align:center;position:relative;">
              <div style="font-size:15px;color:rgba(255,255,255,0.92);margin-bottom:10px;letter-spacing:0.04em;">Welcome · almost there</div>
              <div style="font-size:32px;font-weight:700;color:#ffffff;letter-spacing:-0.02em;line-height:1.2;text-shadow:0 2px 12px rgba(0,0,0,0.12);">{bank_name}</div>
              <div style="margin-top:14px;font-size:15px;color:rgba(255,255,255,0.95);line-height:1.45;max-width:340px;margin-left:auto;margin-right:auto;">
                A tiny step left — confirm your email so we know it&apos;s really you ✨
              </div>
            </td>
          </tr>
          <!-- body -->
          <tr>
            <td style="padding:36px 32px 8px;text-align:center;">
              <p style="margin:0;font-size:18px;line-height:1.6;color:#334155;font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
                Here&apos;s your <strong style="color:#0f766e;">one-time code</strong> — type it in the app to finish opening your account:
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:28px 24px 8px;">
              <table role="presentation" cellspacing="0" cellpadding="0" align="center" style="margin:0 auto;">
                <tr>{digits_row}</tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:8px 32px 28px;text-align:center;">
              <p style="margin:0;font-size:14px;line-height:1.55;color:#64748b;font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
                This code melts away in <strong style="color:#0d9488;">10 minutes</strong> — like morning dew, so please use it soon.
              </p>
            </td>
          </tr>
          <!-- divider hearts -->
          <tr>
            <td style="padding:0 40px;text-align:center;">
              <div style="height:1px;background:linear-gradient(90deg,transparent,#99f6e4,transparent);margin:8px 0 20px;"></div>
              <span style="font-size:18px;line-height:1;color:#99f6e4;" aria-hidden="true">♥</span>
            </td>
          </tr>
          <!-- security card -->
          <tr>
            <td style="padding:0 28px 28px;">
              <div style="background:linear-gradient(135deg,#f0fdfa 0%,#ecfeff 100%);border-radius:16px;padding:20px 22px;border:1px solid #ccfbf1;">
                <p style="margin:0;font-size:14px;line-height:1.55;color:#475569;font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
                  <strong style="color:#0f766e;">Stay safe:</strong> we&apos;ll never call or text asking for this code. Keep it just between you and the app.
                </p>
              </div>
            </td>
          </tr>
          <!-- footer -->
          <tr>
            <td style="padding:0 28px 32px;text-align:center;">
              <p style="margin:0;font-size:12px;line-height:1.65;color:#94a3b8;font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
                Sent with care because someone started signup with this email.<br/>
                Not you? No worries — delete this message and carry on with your day.
              </p>
              <p style="margin:16px 0 0;font-size:11px;color:#cbd5e1;font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
                {bank_name} · Banking that feels a little brighter
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    return subject, plain, html_body


def send_registration_email_otp(to_email: str, otp: str) -> tuple[bool, str, str | None]:
    """
    Send HTML OTP email. Returns (success_flag, message_key, otp_for_json_or_none).

    message_key: 'email_sent' | 'email_failed' | 'email_demo' | 'email_not_configured'
    """
    to_email = (to_email or "").strip()
    if not to_email:
        return False, "email_failed", None

    if not _smtp_credentials_set():
        if getattr(settings, "DEBUG", False):
            logger.info("Email SMTP not configured — demo OTP for %s", to_email)
            return True, "email_demo", otp
        logger.warning("Email SMTP not configured — cannot send OTP to %s", to_email)
        return False, "email_not_configured", None

    subject, plain, html_body = build_registration_otp_email(otp)
    from_email = transactional_from_email()
    if not from_email:
        logger.error(
            "Set BREVO_SENDER_EMAIL (verified Gmail) or DEFAULT_FROM_EMAIL in .env — "
            "SMTP login *@smtp-brevo.com cannot be the From address for inbox delivery."
        )
        return False, "email_failed", None

    msg = EmailMultiAlternatives(
        subject=subject,
        body=plain,
        from_email=from_email,
        to=[to_email],
    )
    msg.attach_alternative(html_body, "text/html")

    try:
        msg.send(fail_silently=False)
        logger.info("Registration email OTP sent to %s", to_email)
        return True, "email_sent", None
    except Exception:
        logger.exception("Registration email OTP failed for %s", to_email)
        if getattr(settings, "DEBUG", False):
            return True, "email_demo", otp
        return False, "email_failed", None
