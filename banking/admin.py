from django.contrib import admin

from .models import BankAccount, Transaction


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ("account_number", "iban", "user", "balance")
    search_fields = ("account_number", "iban", "user__username")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("created_at", "account", "kind", "amount", "balance_after", "user_saved")
    list_filter = ("kind", "user_saved")
    search_fields = ("description", "counterparty_account", "counterparty_iban")
