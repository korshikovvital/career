# Generated by Django 3.2.15 on 2023-04-04 12:45

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vacancies', '0012_vacancyreserve'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('replies', '0005_testdrivedate_testdrivereply'),
    ]

    operations = [
        migrations.CreateModel(
            name='VacancyReserveReply',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('experience', models.CharField(choices=[('from_0_to_3_month', 'От 0 до 3 месяцев'), ('from_3_to_6_month', 'От 3 до 6 месяцев'), ('from_6_to_9_month', 'От 6 до 9 месяцев'), ('from_9_to_12_month', 'От 9 до 12 месяцев'), ('more_then_year', 'От года и больше')], max_length=50, verbose_name='Стаж работы сотрудника в текущей должности')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='vacancy_reserve_replies', to=settings.AUTH_USER_MODEL, verbose_name='Соискатель')),
                ('vacancy_reserve', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='vacancy_reserve_replies', to='vacancies.vacancyreserve', verbose_name='Кадровый резерв')),
            ],
            options={
                'verbose_name': 'Отклик на кадровый резерв',
                'verbose_name_plural': 'Отклики на кадровый резерв',
            },
        ),
    ]