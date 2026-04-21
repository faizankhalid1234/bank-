# SMS OTP removed — email-only verification.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("banking", "0009_alter_userprofile_phone_drop_unique"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="pendingsignup",
            name="otp_hash",
        ),
    ]
