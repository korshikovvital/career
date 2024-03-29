# Generated by Django 3.2.15 on 2022-11-11 10:49

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vacancies', '0007_question_type_added'),
    ]

    operations = [
        migrations.CreateModel(
            name='VacanciesInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=500, verbose_name='Заголовок')),
                ('description', models.TextField(verbose_name='Описание')),
                ('priority', models.PositiveSmallIntegerField(default=10, help_text='Информация с наименьшим значением будет выдаваться первой. Диапазон значений: [1;10]', validators=[django.core.validators.MaxValueValidator(10), django.core.validators.MinValueValidator(1)], verbose_name='Приоритет')),
            ],
            options={
                'verbose_name': 'Частый вопрос',
                'verbose_name_plural': 'Частые вопросы',
            },
        ),
    ]
