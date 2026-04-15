"""Send one test email via Brevo/SMTP (.env) — same path as registration OTP."""

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand

from banking.email_otp import (
    _smtp_credentials_set,
    build_registration_otp_email,
    transactional_from_email,
)


class Command(BaseCommand):
    help = "Send a test HTML email (uses same SMTP + From as signup OTP)."

    def add_arguments(self, parser):
        parser.add_argument(
            "to",
            nargs="?",
            default="",
            help="Recipient email (e.g. your Gmail). Required.",
        )

    def handle(self, *args, **options):
        to = (options["to"] or "").strip()
        if not to or "@" not in to:
            self.stderr.write(self.style.ERROR("Usage: python manage.py send_test_email you@gmail.com"))
            return

        if not _smtp_credentials_set():
            self.stderr.write(
                self.style.ERROR(
                    "SMTP not configured. Set BREVO_SMTP_LOGIN + BREVO_SMTP_KEY (and BREVO_SENDER_EMAIL if login is @smtp-brevo.com)."
                )
            )
            return

        from_email = transactional_from_email()
        if not from_email:
            self.stderr.write(
                self.style.ERROR(
                    "From address missing. .env mein BREVO_SENDER_EMAIL=apna@gmail.com likho "
                    "(Brevo Senders mein verify ho)."
                )
            )
            return

        self.stdout.write(f"From: {from_email}\nTo:   {to}\nSMTP: {settings.EMAIL_HOST_USER} @ {settings.EMAIL_HOST}")

        subject, plain, html_body = build_registration_otp_email("123456", to)
        subject = "[Test] " + subject

        msg = EmailMultiAlternatives(subject, plain, from_email, [to])
        msg.attach_alternative(html_body, "text/html")

        try:
            msg.send(fail_silently=False)
            self.stdout.write(self.style.SUCCESS("Email sent. Check that inbox + Spam/Promotions."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Send failed: {e}"))

