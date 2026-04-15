# Remove email OTP field from pending signup

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("banking", "0005_pending_signup_email_otp"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="pendingsignup",
            name="email_otp_hash",
        ),
    ]
