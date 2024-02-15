# Generated by Django 3.2.15 on 2022-11-02 21:00

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vacancies', '0004_company_app_models_instead_users'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='polltemplate',
            name='vacancy',
        ),
        migrations.AlterField(
            model_name='poll',
            name='vacancy',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='polls', to='vacancies.vacancy', verbose_name='Вакансия'),
        ),
    ]
