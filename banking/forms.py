from decimal import Decimal

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


class AlyAuthForm(AuthenticationForm):
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(attrs={"class": "input", "autocomplete": "username", "placeholder": " "}),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "input", "autocomplete": "current-password", "placeholder": " "}),
    )


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("username", "password1", "password2"):
            self.fields[name].widget.attrs.update({"class": "input", "placeholder": " "})


class AmountForm(forms.Form):
    amount = forms.DecimalField(
        min_value=Decimal("0.01"),
        max_digits=14,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "input", "step": "0.01", "placeholder": "0.00"}),
    )
    description = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "Optional note"}),
    )


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
