# Generated by Django 3.2.16 on 2023-12-04 12:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vacancies', '0020_vacancy_recruiter'),
    ]

    operations = [
        migrations.RenameField(
            model_name='vacancy',
            old_name='referral',
            new_name='is_referral',
        ),
        migrations.RemoveField(
            model_name='vacancy',
            name='selection_type',
        ),
    ]
