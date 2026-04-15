from decimal import Decimal

from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q

from .models import (
    BankAccount,
    Transaction,
    iban_for_account_number,
    next_account_number,
)


def find_recipient(account_or_iban: str) -> BankAccount | None:
    v = account_or_iban.strip().upper().replace(" ", "")
    if v.startswith("ALYBANK"):
        hit = BankAccount.objects.filter(iban=v).first()
        if hit:
            return hit
        suffix = v[7:]
        if suffix.isdigit():
            return BankAccount.objects.filter(account_number=suffix).first()
        return None
    if v.isdigit():
        return (
            BankAccount.objects.filter(account_number=v).first()
            or BankAccount.objects.filter(iban=iban_for_account_number(v)).first()
        )
    return BankAccount.objects.filter(account_number=v).first()


@transaction.atomic
def apply_credit(
    account: BankAccount, amount: Decimal, description: str = ""
) -> Transaction:
    locked = BankAccount.objects.select_for_update().get(pk=account.pk)
    locked.balance += amount
    locked.save(update_fields=["balance"])
    return Transaction.objects.create(
        account=locked,
        kind=Transaction.Kind.CREDIT,
        amount=amount,
        balance_after=locked.balance,
        description=description or "Credit to account",
    )


@transaction.atomic
def apply_debit(
    account: BankAccount, amount: Decimal, description: str = ""
) -> Transaction:
    locked = BankAccount.objects.select_for_update().get(pk=account.pk)
    if locked.balance < amount:
        raise ValueError("Insufficient balance.")
    locked.balance -= amount
    locked.save(update_fields=["balance"])
    return Transaction.objects.create(
        account=locked,
        kind=Transaction.Kind.DEBIT,
        amount=amount,
        balance_after=locked.balance,
        description=description or "Debit from account",
    )


@transaction.atomic
def transfer(
    sender: BankAccount, recipient: BankAccount, amount: Decimal, description: str = ""
) -> tuple[Transaction, Transaction]:
    if sender.pk == recipient.pk:
        raise ValueError("Cannot pay yourself.")
    s = BankAccount.objects.select_for_update().get(pk=sender.pk)
    r = BankAccount.objects.select_for_update().get(pk=recipient.pk)
    if s.balance < amount:
        raise ValueError("Insufficient balance.")
    s.balance -= amount
    r.balance += amount
    s.save(update_fields=["balance"])
    r.save(update_fields=["balance"])
    ref = description or "Transfer"
    out_tx = Transaction.objects.create(
        account=s,
        kind=Transaction.Kind.PAYMENT_SENT,
        amount=amount,
        balance_after=s.balance,
        description=ref,
        counterparty_account=r.account_number,
        counterparty_iban=r.iban,
    )
    in_tx = Transaction.objects.create(
        account=r,
        kind=Transaction.Kind.PAYMENT_RECEIVED,
        amount=amount,
        balance_after=r.balance,
        description=ref,
        counterparty_account=s.account_number,
        counterparty_iban=s.iban,
    )
    return out_tx, in_tx


def ensure_bank_account(user: User) -> BankAccount:
    existing = BankAccount.objects.filter(user=user).first()
    if existing:
        return existing
    num = next_account_number()
    return BankAccount.objects.create(
        user=user,
        account_number=num,
        iban=iban_for_account_number(num),
    )
