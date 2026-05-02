from django.contrib import admin, messages
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import path

from .forms import StaffLedgerAdjustmentForm
from .models import BankAccount, PendingSignup, Transaction, UserProfile
from .services import apply_credit, apply_debit


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone")
    search_fields = ("phone", "user__username", "user__email")
    ordering = ("id",)


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ("account_number", "iban", "user", "balance")
    list_select_related = ("user",)
    search_fields = ("account_number", "iban", "user__username", "user__email")
    readonly_fields = ("account_number", "iban", "balance")
    ordering = ("account_number",)
    change_list_template = "admin/banking/bankaccount/change_list.html"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_urls(self):
        urls = super().get_urls()
        info = self.model._meta.app_label, self.model._meta.model_name
        custom = [
            path(
                "adjust-ledger/",
                self.admin_site.admin_view(self.adjust_ledger_view),
                name="%s_%s_adjust_ledger" % info,
            ),
        ]
        return custom + urls

    def adjust_ledger_view(self, request):
        """Apply credit or debit to a customer account; balance_after is set automatically."""
        if request.method == "POST":
            form = StaffLedgerAdjustmentForm(request.POST)
            if form.is_valid():
                account = form.cleaned_data["account"]
                amount = form.cleaned_data["amount"]
                kind = form.cleaned_data["kind"]
                desc = (form.cleaned_data.get("description") or "").strip()
                try:
                    with transaction.atomic():
                        if kind == StaffLedgerAdjustmentForm.KIND_CREDIT:
                            ref = desc or "Staff credit (admin)"
                            apply_credit(account, amount, ref)
                        else:
                            ref = desc or "Staff debit (admin)"
                            apply_debit(account, amount, ref)
                        account.refresh_from_db()
                except ValueError as e:
                    messages.error(request, str(e))
                    return redirect(request.path)
                messages.success(
                    request,
                    "Ledger updated. Account %s — new balance PKR %s (after balance recorded on the transaction)."
                    % (account.account_number, account.balance),
                )
                return redirect("admin:banking_bankaccount_changelist")
        else:
            form = StaffLedgerAdjustmentForm()
        return render(
            request,
            "admin/banking/bankaccount/adjust_ledger.html",
            {
                **self.admin_site.each_context(request),
                "title": "Credit / debit customer account",
                "form": form,
                "opts": self.model._meta,
                "has_view_permission": True,
            },
        )


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "account",
        "kind",
        "amount",
        "balance_after",
        "description",
        "user_saved",
    )
    list_filter = ("kind", "user_saved")
    search_fields = ("description", "counterparty_account", "counterparty_iban")
    readonly_fields = (
        "account",
        "kind",
        "amount",
        "balance_after",
        "description",
        "counterparty_account",
        "counterparty_iban",
        "user_saved",
        "created_at",
    )
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(PendingSignup)
class PendingSignupAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "phone_number", "expires_at", "created_at")
    search_fields = ("username", "email", "phone_number")
    readonly_fields = (
        "id",
        "username",
        "email",
        "phone_number",
        "password_hash",
        "email_otp_hash",
        "expires_at",
        "created_at",
    )
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False
