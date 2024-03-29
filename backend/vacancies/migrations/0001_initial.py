# Generated by Django 3.2.15 on 2022-10-14 08:36

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import core.utils


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0004_city'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.ImageField(upload_to=core.utils.file_path, verbose_name='Изображение')),
            ],
            options={
                'verbose_name': 'Изображение',
                'verbose_name_plural': 'Изображения',
            },
        ),
        migrations.CreateModel(
            name='Vacancy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=512, verbose_name='Название вакансии')),
                ('hot', models.BooleanField(default=False, verbose_name='Горящая вакансия')),
                ('rate', models.CharField(blank=True, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('E', 'E')], max_length=20, null=True, verbose_name='Требуемый уровень')),
                ('duties', models.TextField(blank=True, help_text='Задачи/должностные обязанности', null=True, verbose_name='Задачи')),
                ('skills', models.TextField(blank=True, help_text='Умения/навыки/опыт', null=True, verbose_name='Ожидания')),
                ('benefits', models.TextField(blank=True, help_text='Предлагаемые плюшки (печеньки/кофе/дружный коллектив)', null=True, verbose_name='Мы предлагаем')),
            ],
            options={
                'verbose_name': 'Вакансия',
                'verbose_name_plural': 'Вакансии',
            },
        ),
        migrations.CreateModel(
            name='VacancyToImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vacancies.image', verbose_name='Изображение')),
                ('vacancy', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vacancies.vacancy', verbose_name='Вакансия')),
            ],
        ),
        migrations.CreateModel(
            name='VacancyToCity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('city', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.city', verbose_name='Город')),
                ('vacancy', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vacancies.vacancy', verbose_name='Вакансия')),
            ],
        ),
        migrations.AddField(
            model_name='vacancy',
            name='cities',
            field=models.ManyToManyField(related_name='vacancies', through='vacancies.VacancyToCity', to='users.City', verbose_name='Города'),
        ),
        migrations.AddField(
            model_name='vacancy',
            name='images',
            field=models.ManyToManyField(related_name='vacancies', through='vacancies.VacancyToImage', to='vacancies.Image', verbose_name='Фото офиса'),
        ),
        migrations.AddField(
            model_name='vacancy',
            name='manager',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Руководитель'),
        ),
    ]
