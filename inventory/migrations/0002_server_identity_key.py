from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('inventory', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='server',
            name='identity_key',
            field=models.CharField(
                max_length=192, unique=True, null=True,
                blank=True, editable=False,
            ),
        ),
    ]
