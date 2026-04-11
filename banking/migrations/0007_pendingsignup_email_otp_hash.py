from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("banking", "0006_remove_pendingsignup_email_otp_hash"),
    ]

    operations = [
        migrations.AddField(
            model_name="pendingsignup",
            name="email_otp_hash",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
    ]
