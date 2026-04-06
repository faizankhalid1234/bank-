import django.db.models.deletion
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="BankAccount",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("account_number", models.CharField(db_index=True, max_length=32, unique=True)),
                ("iban", models.CharField(db_index=True, max_length=34, unique=True)),
                ("balance", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=14)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="bank_account",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="Transaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(choices=[("credit", "Credit"), ("debit", "Debit"), ("payment_sent", "Payment sent"), ("payment_received", "Payment received")], max_length=32)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=14)),
                ("balance_after", models.DecimalField(decimal_places=2, max_digits=14)),
                ("description", models.CharField(blank=True, max_length=255)),
                ("counterparty_account", models.CharField(blank=True, max_length=32)),
                ("counterparty_iban", models.CharField(blank=True, max_length=34)),
                ("user_saved", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="transactions",
                        to="banking.bankaccount",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at", "-id"],
            },
        ),
    ]
