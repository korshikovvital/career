# Generated by Django 3.2.15 on 2022-10-24 12:07

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_auto_20221024_1207'),
        ('vacancies', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='vacancy',
            name='company_unit',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='users.companyunit', verbose_name='Подразделение'),
        ),
        migrations.AddField(
            model_name='vacancy',
            name='position',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='users.position', verbose_name='Должность'),
        ),
    ]
