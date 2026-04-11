from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("banking", "0007_pendingsignup_email_otp_hash"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userprofile",
            name="phone",
            field=models.CharField(db_index=True, max_length=20, unique=True),
        ),
    ]
