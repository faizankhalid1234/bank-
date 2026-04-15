"""Send one test SMS via Twilio using project .env (TWILIO_*)."""

import json

from django.conf import settings
from django.core.management.base import BaseCommand

from banking.phone_utils import normalize_phone, validate_phone_e164
from banking.sms import _twilio_configured, _twilio_send


class Command(BaseCommand):
    help = "Send a test SMS through Twilio (credentials from .env next to manage.py)."

    def add_arguments(self, parser):
        parser.add_argument(
            "phone",
            nargs="?",
            default="+923029655325",
            help="Recipient (PK: 03xx... or +923...). Default: +923029655325",
        )
        parser.add_argument(
            "-m",
            "--message",
            default="AlyBank test: Twilio SMS is working. Reply STOP to opt out.",
            help="SMS body text",
        )

    def handle(self, *args, **options):
        raw = (options["phone"] or "").strip()
        to_e164 = normalize_phone(raw)
        if not validate_phone_e164(to_e164):
            self.stderr.write(
                self.style.ERROR(f"Invalid phone after normalize: {to_e164!r}")
            )
            return

        if not _twilio_configured():
            self.stderr.write(
                self.style.ERROR(
                    "Twilio not configured. Set TWILIO_ACCOUNT_SID, TWILIO_FROM_NUMBER, "
                    "and TWILIO_AUTH_TOKEN (or API Key + Secret) in .env"
                )
            )
            return

        from_num = (settings.TWILIO_FROM_NUMBER or "").strip()
        body = options["message"]

        self.stdout.write(f"From: {from_num}\nTo:   {to_e164}\nSending…")

        ok, err = _twilio_send(from_num, to_e164, body)
        if ok:
            self.stdout.write(self.style.SUCCESS("SMS sent OK. Check your phone."))
        else:
            self.stderr.write(
                self.style.ERROR(f"Twilio error: {err[:800] if err else 'unknown'}")
            )
            code = None
            try:
                code = int((json.loads(err or "{}") or {}).get("code"))
            except (TypeError, ValueError, json.JSONDecodeError):
                pass
            if code == 21608:
                self.stdout.write("")
                self.stdout.write(
                    self.style.WARNING(
                        "Trial account: yeh number Twilio par VERIFIED nahi hai.\n"
                        "  1) Browser kholo: https://console.twilio.com/us1/develop/phone-numbers/manage/verified\n"
                        "  2) 'Add a new Caller ID' → apna poora number E.164 mein (e.g. +923029655325)\n"
                        "  3) SMS se code verify karo\n"
                        "  4) Phir dubara: python manage.py send_test_sms\n\n"
                        "Ya Twilio account upgrade karo / paid number lo — tab zyada numbers par bhej sakte ho.\n"
                    )
                )
