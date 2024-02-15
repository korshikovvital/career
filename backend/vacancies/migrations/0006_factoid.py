# Generated by Django 3.2.15 on 2022-11-08 11:46

from django.db import migrations, models

import core.utils


class Migration(migrations.Migration):

    dependencies = [
        ('vacancies', '0005_poll_o2o_poll_template_removed_fk_vacancy'),
    ]

    operations = [
        migrations.CreateModel(
            name='Factoid',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.ImageField(upload_to=core.utils.file_path, verbose_name='Фактоид')),
            ],
            options={
                'verbose_name': 'Фактоид',
                'verbose_name_plural': 'Фактоиды',
            },
        ),
    ]
