from decimal import Decimal

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.db import transaction
from .models import BankAccount, UserProfile
from .phone_utils import normalize_phone, validate_phone_e164


class AlyAuthForm(AuthenticationForm):
    username = forms.CharField(
        label="Username",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "input",
                "autocomplete": "username",
                "placeholder": " ",
            }
        ),
    )
    email = forms.EmailField(
        label="Email",
        required=False,
        widget=forms.EmailInput(
            attrs={
                "class": "input",
                "autocomplete": "email",
                "placeholder": "you@example.com",
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "input", "autocomplete": "current-password", "placeholder": " "}),
    )

    def clean(self):
        username_raw = (self.cleaned_data.get("username") or "").strip()
        email_raw = (self.cleaned_data.get("email") or "").strip()

        if username_raw:
            self.cleaned_data["username"] = username_raw
        elif email_raw:
            user_lookup = User.objects.filter(email__iexact=email_raw).first()
            if user_lookup is None:
                raise forms.ValidationError(
                    {"email": "No account found with that email address."}
                )
            self.cleaned_data["username"] = user_lookup.username
        else:
            raise forms.ValidationError("Enter your username or email address.")

        return super().clean()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="Email",
        widget=forms.EmailInput(
            attrs={"class": "input", "placeholder": " ", "autocomplete": "email"}
        ),
    )
    phone = forms.CharField(
        label="Mobile number",
        required=True,
        max_length=20,
        widget=forms.TextInput(
            attrs={
                "class": "input",
                "placeholder": "+923001234567",
                "autocomplete": "tel",
            }
        ),
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    field_order = ["username", "email", "phone", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("username", "password1", "password2"):
            self.fields[name].widget.attrs.update({"class": "input", "placeholder": " "})
        self.fields["email"].widget.attrs.setdefault("class", "input")

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with that email already exists.")
        return email

    def clean_phone(self):
        raw = self.cleaned_data.get("phone") or ""
        p = normalize_phone(raw)
        if not validate_phone_e164(p):
            raise forms.ValidationError(
                "Enter a valid mobile number with country code, e.g. +923001234567 or 03001234567."
            )
        return p

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            phone = self.cleaned_data["phone"]
            UserProfile.objects.update_or_create(user=user, defaults={"phone": phone})
        return user


class PaymentForm(forms.Form):
    to_account_or_iban = forms.CharField(
        max_length=40,
        label="To account or IBAN",
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "Account number or IBAN"}),
    )
    amount = forms.DecimalField(
        min_value=Decimal("0.01"),
        max_digits=14,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "input", "step": "0.01", "placeholder": "0.00"}),
    )
    description = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "Payment reference"}),
    )

    def clean_to_account_or_iban(self):
        raw = self.cleaned_data["to_account_or_iban"].strip().upper().replace(" ", "")
        if not raw:
            raise forms.ValidationError("Enter an account number or IBAN.")
        return raw


class StaffLedgerAdjustmentForm(forms.Form):
    """Staff-only: credit or debit any customer account. Balance updates via ledger services."""

    KIND_CREDIT = "credit"
    KIND_DEBIT = "debit"

    account = forms.ModelChoiceField(
        label="Customer account",
        queryset=BankAccount.objects.select_related("user").order_by("account_number"),
        empty_label=None,
    )
    kind = forms.ChoiceField(
        label="Type",
        choices=[
            (KIND_CREDIT, "Credit — add funds to balance"),
            (KIND_DEBIT, "Debit — remove funds from balance"),
        ],
        initial=KIND_CREDIT,
    )
    amount = forms.DecimalField(
        label="Amount (PKR)",
        min_value=Decimal("0.01"),
        max_digits=14,
        decimal_places=2,
    )
    description = forms.CharField(
        label="Note (optional)",
        max_length=255,
        required=False,
        strip=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        acct = self.fields["account"]
        acct.label_from_instance = lambda obj: (
            f"{obj.account_number} — {obj.user.get_username()} (PKR {obj.balance})"
        )
