from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("banking", "0008_userprofile_phone_unique"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userprofile",
            name="phone",
            field=models.CharField(db_index=True, max_length=20),
        ),
    ]
