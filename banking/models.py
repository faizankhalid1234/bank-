import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Max


class UserProfile(models.Model):
    """Verified phone at signup (OTP)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    phone = models.CharField(max_length=20, db_index=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.user.username} ({self.phone})"


class BankAccount(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bank_account",
    )
    account_number = models.CharField(max_length=32, unique=True, db_index=True)
    iban = models.CharField(max_length=34, unique=True, db_index=True)
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.account_number} ({self.user.username})"


class Transaction(models.Model):
    class Kind(models.TextChoices):
        CREDIT = "credit", "Credit"
        DEBIT = "debit", "Debit"
        PAYMENT_SENT = "payment_sent", "Payment sent"
        PAYMENT_RECEIVED = "payment_received", "Payment received"

    account = models.ForeignKey(
        BankAccount,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    kind = models.CharField(max_length=32, choices=Kind.choices)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    balance_after = models.DecimalField(max_digits=14, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    counterparty_account = models.CharField(max_length=32, blank=True)
    counterparty_iban = models.CharField(max_length=34, blank=True)
    user_saved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.kind} {self.amount} @ {self.created_at}"


def next_account_number() -> str:
    start = 1_000_000_000
    rows = BankAccount.objects.values_list("account_number", flat=True)
    best = start - 1
    for s in rows:
        try:
            best = max(best, int(s))
        except ValueError:
            continue
    return str(best + 1) if best >= start else str(start)


def iban_for_account_number(account_number: str) -> str:
    if account_number == "1000000000":
        return "ALYBANK10000000000"
    return f"ALYBANK{account_number}"


class PendingSignup(models.Model):
    """Holds registration data until SMS + email OTPs are verified."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150)
    email = models.EmailField(blank=True, default="")
    phone_number = models.CharField(max_length=20, db_index=True, default="", blank=True)
    password_hash = models.CharField(max_length=128)
    otp_hash = models.CharField(max_length=64)  # SMS code
    email_otp_hash = models.CharField(max_length=64, default="", blank=True)
    expires_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
