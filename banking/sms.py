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
    """True if we can call Twilio Messages API (Account SID + auth + From or Messaging Service)."""
    acct = (getattr(settings, "TWILIO_ACCOUNT_SID", "") or "").strip()
    if not acct:
        return False
    frm = (getattr(settings, "TWILIO_FROM_NUMBER", "") or "").strip()
    msid = (getattr(settings, "TWILIO_MESSAGING_SERVICE_SID", "") or "").strip()
    if not frm and not msid:
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


# Twilio REST: common codes when trial / recipient / permission (see Twilio error dictionary).
_TRIAL_OR_RECIPIENT_CODES = frozenset(
    {21211, 21408, 21608, 21610, 21614, 21659, 60203, 60212}
)


def send_registration_otp(
    phone_e164: str, otp: str
) -> tuple[bool, str, str | None, int | None]:
    """
    Try to SMS the OTP. Returns (success, user_message_key, otp_for_json_or_none, twilio_error_code).

    user_message_key:
      'sms_sent' | 'sms_failed' | 'sms_trial_unverified' | 'sms_demo' | 'sms_dev_console'

    When Twilio is not configured and DEBUG is True, otp_for_json_or_none is the OTP
    so the SPA can show it (demo). When DEBUG is False, OTP is never returned.

    When Twilio is configured but send fails, we return sms_trial_unverified or sms_failed
    (never pretend sms_sent). Optional: SMS_OTP_FALLBACK_ON_TWILIO_FAIL=1 with DEBUG returns
    sms_demo + OTP for local trial debugging only.
    """
    from_num = (getattr(settings, "TWILIO_FROM_NUMBER", "") or "").strip()
    messaging_sid = (getattr(settings, "TWILIO_MESSAGING_SERVICE_SID", "") or "").strip()
    body = f"AlyBank verification code: {otp}. Valid 10 minutes. Do not share."

    if _twilio_configured():
        ok, err = _twilio_send(from_num, messaging_sid, phone_e164, body)
        if ok:
            logger.info("SMS OTP sent to %s", phone_e164)
            return True, "sms_sent", None, None
        logger.warning("Twilio SMS failed: %s", err)
        code = _twilio_error_code(err)
        _fallback = getattr(settings, "SMS_OTP_FALLBACK_ON_TWILIO_FAIL", False)
        if getattr(settings, "DEBUG", False) and _fallback:
            logger.info("Twilio failure + SMS_OTP_FALLBACK_ON_TWILIO_FAIL: demo OTP for %s", phone_e164)
            return True, "sms_demo", otp, code
        if code in _TRIAL_OR_RECIPIENT_CODES:
            return False, "sms_trial_unverified", None, code
        return False, "sms_failed", None, code

    if getattr(settings, "DEBUG", False):
        logger.info("Demo mode (no Twilio): OTP for %s shown in app only", phone_e164)
        return True, "sms_demo", otp, None

    logger.warning(
        "SMS not configured — OTP for %s is: %s (server log only; set TWILIO_* or run with DEBUG)",
        phone_e164,
        otp,
    )
    return True, "sms_dev_console", None, None


def _twilio_send(
    from_number: str, messaging_service_sid: str, to_number: str, body: str
) -> tuple[bool, str]:
    acct_sid = settings.TWILIO_ACCOUNT_SID
    url = f"https://api.twilio.com/2010-04-01/Accounts/{acct_sid}/Messages.json"
    fields: dict[str, str] = {"To": to_number, "Body": body}
    msid = (messaging_service_sid or "").strip()
    if msid:
        fields["MessagingServiceSid"] = msid
    else:
        fields["From"] = from_number
    data = urlencode(fields).encode()
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
