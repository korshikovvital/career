# Generated by Django 3.2.15 on 2022-11-07 03:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_replace_models_to_company_app'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='reserved_until',
            field=models.DateTimeField(blank=True, null=True, verbose_name='В резерве до'),
        ),
    ]