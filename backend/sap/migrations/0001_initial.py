# Generated by Django 3.2.16 on 2023-10-18 10:20

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SapRequest',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('guid', models.CharField(max_length=120, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('Ошибка', 'Error'), ('Успешно', 'Success'), ('Отправлен', 'Sent')], max_length=120)),
                ('request_body', models.JSONField(blank=True, default=dict, null=True)),
                ('response_sap', models.JSONField(blank=True, default=dict, null=True)),
            ],
            options={
                'verbose_name': 'Запрос в Sap',
                'verbose_name_plural': 'Запросы в Sap',
            },
        ),
    ]
