import re


def normalize_phone(raw: str) -> str:
    """Normalize to E.164-style +digits (PK-friendly: 03xx → +92)."""
    s = (raw or "").strip()
    s = re.sub(r"[\s\-]", "", s)
    digits_only = re.sub(r"\D", "", s)
    if not digits_only:
        return ""
    if s.startswith("+"):
        return "+" + digits_only
    if digits_only.startswith("92") and len(digits_only) >= 12:
        return "+" + digits_only
    if digits_only.startswith("0") and len(digits_only) >= 10:
        return "+92" + digits_only[1:]
    if len(digits_only) == 10 and digits_only.startswith("3"):
        return "+92" + digits_only
    if len(digits_only) >= 10:
        return "+" + digits_only
    return "+" + digits_only


def validate_phone_e164(phone: str) -> bool:
    if not phone or not phone.startswith("+"):
        return False
    d = re.sub(r"\D", "", phone[1:])
    return 10 <= len(d) <= 15


def mask_phone(phone_e164: str) -> str:
    """Short display for UI (e.g. +92******3210)."""
    s = (phone_e164 or "").strip()
    if len(s) <= 8:
        return "****"
    return s[:3] + "******" + s[-4:]
