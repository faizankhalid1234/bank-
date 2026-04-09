"""Send OTP via Twilio when configured; otherwise log only (never expose OTP in HTTP)."""

import base64
import json
import logging
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings

logger = logging.getLogger(__name__)


def send_registration_otp(phone_e164: str, otp: str) -> tuple[bool, str, str | None]:
    """
    Try to SMS the OTP. Returns (success, user_message_key, otp_for_json_or_none).

    user_message_key:
      'sms_sent' | 'sms_failed' | 'sms_trial_unverified' | 'sms_demo' | 'sms_dev_console'

    When Twilio is not configured and DEBUG is True, otp_for_json_or_none is the OTP
    so the SPA can show it (demo). When DEBUG is False, OTP is never returned.
    """
    sid = getattr(settings, "TWILIO_ACCOUNT_SID", "") or ""
    token = getattr(settings, "TWILIO_AUTH_TOKEN", "") or ""
    from_num = getattr(settings, "TWILIO_FROM_NUMBER", "") or ""
    body = f"AlyBank verification code: {otp}. Valid 10 minutes. Do not share."

    if sid and token and from_num:
        ok, err = _twilio_send(from_num, phone_e164, body)
        if ok:
            logger.info("SMS OTP sent to %s", phone_e164)
            return True, "sms_sent", None
        logger.warning("Twilio SMS failed: %s", err)
        if _twilio_error_code(err) == 21608:
            return False, "sms_trial_unverified", None
        return False, "sms_failed", None

    if getattr(settings, "DEBUG", False):
        logger.info("Demo mode (no Twilio): OTP for %s shown in app only", phone_e164)
        return True, "sms_demo", otp

    logger.warning(
        "SMS not configured — OTP for %s is: %s (server log only; set TWILIO_* or run with DEBUG)",
        phone_e164,
        otp,
    )
    return True, "sms_dev_console", None


def _twilio_send(from_number: str, to_number: str, body: str) -> tuple[bool, str]:
    sid = settings.TWILIO_ACCOUNT_SID
    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    data = urlencode(
        {
            "To": to_number,
            "From": from_number,
            "Body": body,
        }
    ).encode()
    req = Request(url, data=data, method="POST")
    auth = base64.b64encode(f"{sid}:{settings.TWILIO_AUTH_TOKEN}".encode()).decode()
    req.add_header("Authorization", f"Basic {auth}")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urlopen(req, timeout=30) as resp:
            if resp.status in (200, 201):
                return True, ""
            return False, resp.read().decode(errors="replace")
    except HTTPError as e:
        return False, e.read().decode(errors="replace")
    except URLError as e:
        return False, str(e.reason)


def _twilio_error_code(err_text: str) -> int | None:
    try:
        data = json.loads(err_text or "")
    except Exception:
        return None
    code = data.get("code")
    return int(code) if isinstance(code, int) else None
