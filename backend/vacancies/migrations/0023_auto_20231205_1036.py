# Generated by Django 3.2.16 on 2023-12-05 10:36

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('vacancies', '0022_auto_20231205_0934'),
    ]

    operations = [
        migrations.CreateModel(
            name='VacancyViewed',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.ForeignKey(help_text='Кто просмотрел', on_delete=django.db.models.deletion.CASCADE, related_name='viewed_vacancies', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
                ('vacancy', models.ForeignKey(help_text='Просмотренная вакансия', on_delete=django.db.models.deletion.CASCADE, related_name='viewed_users', to='vacancies.vacancy', verbose_name='Вакансия')),
            ],
            options={
                'verbose_name': 'Просмотренная вакансия',
                'verbose_name_plural': 'Просмотренные вакансии',
            },
        ),
        migrations.AddConstraint(
            model_name='vacancyviewed',
            constraint=models.UniqueConstraint(fields=('user', 'vacancy'), name='vacancies_vacancyviewed_is_one_user_to_view_vacancy'),
        ),
    ]
