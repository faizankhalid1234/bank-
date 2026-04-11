"""Send OTP via Twilio when configured; otherwise log only (never expose OTP in HTTP)."""

import base64
import json
import logging
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings

logger = logging.getLogger(__name__)


def _twilio_configured() -> bool:
    """True if we can call Twilio Messages API (Account SID + From + auth)."""
    acct = (getattr(settings, "TWILIO_ACCOUNT_SID", "") or "").strip()
    frm = (getattr(settings, "TWILIO_FROM_NUMBER", "") or "").strip()
    if not acct or not frm:
        return False
    key_sid = (getattr(settings, "TWILIO_API_KEY_SID", "") or "").strip()
    key_secret = (getattr(settings, "TWILIO_API_KEY_SECRET", "") or "").strip()
    if key_sid and key_secret:
        return True
    tok = (getattr(settings, "TWILIO_AUTH_TOKEN", "") or "").strip()
    return bool(tok)


def _twilio_basic_auth_header() -> str:
    key_sid = (getattr(settings, "TWILIO_API_KEY_SID", "") or "").strip()
    key_secret = (getattr(settings, "TWILIO_API_KEY_SECRET", "") or "").strip()
    if key_sid and key_secret:
        raw = f"{key_sid}:{key_secret}"
    else:
        raw = f"{settings.TWILIO_ACCOUNT_SID}:{settings.TWILIO_AUTH_TOKEN}"
    return f"Basic {base64.b64encode(raw.encode()).decode()}"


# Twilio REST: common codes when trial / recipient not allowed (see Twilio docs).
_TRIAL_OR_RECIPIENT_CODES = frozenset({21608, 21211, 21610, 21614, 21408})


def send_registration_otp(phone_e164: str, otp: str) -> tuple[bool, str, str | None]:
    """
    Try to SMS the OTP. Returns (success, user_message_key, otp_for_json_or_none).

    user_message_key:
      'sms_sent' | 'sms_failed' | 'sms_trial_unverified' | 'sms_demo' | 'sms_dev_console'

    When Twilio is not configured and DEBUG is True, otp_for_json_or_none is the OTP
    so the SPA can show it (demo). When DEBUG is False, OTP is never returned.

    When Twilio is configured but the API or message status fails, DEBUG=True still
    returns sms_demo with the OTP so signup is not blocked (trial limits, outages).
    """
    from_num = getattr(settings, "TWILIO_FROM_NUMBER", "") or ""
    body = f"AlyBank verification code: {otp}. Valid 10 minutes. Do not share."

    if _twilio_configured():
        ok, err = _twilio_send(from_num, phone_e164, body)
        if ok:
            logger.info("SMS OTP sent to %s", phone_e164)
            return True, "sms_sent", None
        logger.warning("Twilio SMS failed: %s", err)
        # DEBUG: never hard-fail signup — show OTP in app if SMS cannot be delivered.
        if getattr(settings, "DEBUG", False):
            logger.info("Twilio failure fallback to demo OTP for %s", phone_e164)
            return True, "sms_demo", otp
        code = _twilio_error_code(err)
        if code in _TRIAL_OR_RECIPIENT_CODES:
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
    acct_sid = settings.TWILIO_ACCOUNT_SID
    url = f"https://api.twilio.com/2010-04-01/Accounts/{acct_sid}/Messages.json"
    data = urlencode(
        {
            "To": to_number,
            "From": from_number,
            "Body": body,
        }
    ).encode()
    req = Request(url, data=data, method="POST")
    req.add_header("Authorization", _twilio_basic_auth_header())
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urlopen(req, timeout=30) as resp:
            raw = resp.read().decode(errors="replace")
            if resp.status not in (200, 201):
                return False, raw
            # 201 can still mean Twilio accepted then failed (error_code / status).
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                return True, ""
            st = (payload.get("status") or "").lower()
            if st in ("failed", "undelivered", "canceled"):
                return False, raw
            err_c = payload.get("error_code")
            if err_c is not None and err_c != 0 and err_c != "":
                return False, raw
            return True, ""
    except HTTPError as e:
        return False, e.read().decode(errors="replace")
    except URLError as e:
        return False, str(e.reason)


def _twilio_error_code(err_text: str) -> int | None:
    text = err_text or ""
    try:
        data = json.loads(text)
    except Exception:
        m = re.search(r'"code"\s*:\s*(\d+)', text)
        return int(m.group(1)) if m else None
    code = data.get("code")
    if isinstance(code, int):
        return code
    if isinstance(code, str) and code.isdigit():
        return int(code)
    ec = data.get("error_code")
    if isinstance(ec, int):
        return ec
    if isinstance(ec, str) and ec.isdigit():
        return int(ec)
    return None
