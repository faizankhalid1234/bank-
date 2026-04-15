# Generated manually for dual OTP registration

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("banking", "0004_alter_userprofile_phone"),
    ]

    operations = [
        migrations.AddField(
            model_name="pendingsignup",
            name="email_otp_hash",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
    ]
