# Generated by Django 3.2.16 on 2023-11-09 13:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0003_auto_20231030_1808'),
    ]

    operations = [
        migrations.AlterField(
            model_name='city',
            name='sap_id',
            field=models.CharField(max_length=150, null=True, verbose_name='Id города sap'),
        ),
        migrations.AlterField(
            model_name='office',
            name='sap_city_id',
            field=models.CharField(max_length=150, verbose_name='Id города sap'),
        ),
        migrations.AlterField(
            model_name='office',
            name='sap_id',
            field=models.CharField(max_length=150, verbose_name='Id код офиса'),
        ),
    ]
