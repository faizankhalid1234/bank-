from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from .forms import AlyAuthForm, AmountForm, PaymentForm, RegisterForm
from .models import BankAccount, Transaction
from .services import apply_credit, apply_debit, ensure_bank_account, find_recipient, transfer


def landing(request):
    if request.user.is_authenticated:
        return redirect("banking:dashboard")
    return render(request, "banking/landing.html")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("banking:dashboard")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user: User = form.save()
            try:
                ensure_bank_account(user)
            except IntegrityError:
                messages.error(request, "Could not create account. Try again.")
                return render(request, "banking/register.html", {"form": form})
            login(request, user)
            messages.success(request, "Welcome to AlyBank. Your account is ready.")
            return redirect("banking:dashboard")
    else:
        form = RegisterForm()
    return render(request, "banking/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("banking:dashboard")
    if request.method == "POST":
        form = AlyAuthForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            ensure_bank_account(user)
            return redirect("banking:dashboard")
    else:
        form = AlyAuthForm()
    return render(request, "banking/login.html", {"form": form})


@login_required
def dashboard(request):
    account = ensure_bank_account(request.user)
    recent = account.transactions.all()[:8]
    return render(
        request,
        "banking/dashboard.html",
        {"account": account, "recent": recent},
    )


@login_required
@require_http_methods(["GET", "POST"])
def credit_view(request):
    account = ensure_bank_account(request.user)
    if request.method == "POST":
        form = AmountForm(request.POST)
        if form.is_valid():
            apply_credit(account, form.cleaned_data["amount"], form.cleaned_data.get("description") or "")
            messages.success(request, "Amount credited successfully.")
            return redirect("banking:dashboard")
    else:
        form = AmountForm()
    return render(request, "banking/credit.html", {"form": form, "account": account})


@login_required
@require_http_methods(["GET", "POST"])
def debit_view(request):
    account = ensure_bank_account(request.user)
    if request.method == "POST":
        form = AmountForm(request.POST)
        if form.is_valid():
            try:
                apply_debit(account, form.cleaned_data["amount"], form.cleaned_data.get("description") or "")
            except ValueError:
                messages.error(request, "Insufficient balance for this debit.")
                return render(request, "banking/debit.html", {"form": form, "account": account})
            messages.success(request, "Amount debited successfully.")
            return redirect("banking:dashboard")
    else:
        form = AmountForm()
    return render(request, "banking/debit.html", {"form": form, "account": account})


@login_required
@require_http_methods(["GET", "POST"])
def payment_view(request):
    account = ensure_bank_account(request.user)
    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            raw = form.cleaned_data["to_account_or_iban"]
            recipient = find_recipient(raw)
            if recipient is None:
                messages.error(request, "No AlyBank account found for that number or IBAN.")
                return render(request, "banking/payment.html", {"form": form, "account": account})
            if recipient.pk == account.pk:
                messages.error(request, "You cannot send a payment to your own account.")
                return render(request, "banking/payment.html", {"form": form, "account": account})
            try:
                out_tx, _ = transfer(
                    account,
                    recipient,
                    form.cleaned_data["amount"],
                    form.cleaned_data.get("description") or "",
                )
            except ValueError as e:
                messages.error(request, str(e))
                return render(request, "banking/payment.html", {"form": form, "account": account})
            return redirect("banking:receipt", pk=out_tx.pk)
    else:
        form = PaymentForm()
    return render(request, "banking/payment.html", {"form": form, "account": account})


@login_required
def receipt(request, pk):
    account = ensure_bank_account(request.user)
    tx = get_object_or_404(Transaction, pk=pk, account=account)
    return render(request, "banking/receipt.html", {"tx": tx, "account": account})


@login_required
@require_POST
def save_receipt(request, pk):
    account = ensure_bank_account(request.user)
    tx = get_object_or_404(Transaction, pk=pk, account=account)
    tx.user_saved = True
    tx.save(update_fields=["user_saved"])
    messages.success(request, "Receipt saved to your list.")
    return redirect("banking:history")


@login_required
def history(request):
    account = ensure_bank_account(request.user)
    qs = account.transactions.all()
    saved_only = request.GET.get("saved") == "1"
    if saved_only:
        qs = qs.filter(user_saved=True)
    return render(
        request,
        "banking/history.html",
        {"transactions": qs, "account": account, "saved_only": saved_only},
    )


@login_required
@require_POST
def unsave_receipt(request, pk):
    account = ensure_bank_account(request.user)
    tx = get_object_or_404(Transaction, pk=pk, account=account)
    tx.user_saved = False
    tx.save(update_fields=["user_saved"])
    messages.info(request, "Removed from saved receipts.")
    return redirect("banking:history")
