# Generated by Django 3.2.15 on 2022-10-24 12:07

import django.db.models.deletion
import mptt.fields
from django.db import migrations, models

import core.utils


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_city'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompanyUnit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=512, verbose_name='Название')),
                ('code', models.CharField(blank=True, max_length=20, null=True, verbose_name='Код подразделения')),
                ('lft', models.PositiveIntegerField(editable=False)),
                ('rght', models.PositiveIntegerField(editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(editable=False)),
                ('parent', mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='users.companyunit')),
            ],
            options={
                'verbose_name': 'Подразделение компании',
                'verbose_name_plural': 'Подразделения компании',
            },
        ),
        migrations.CreateModel(
            name='InfoFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('file', models.FileField(upload_to=core.utils.file_path, verbose_name='Файл')),
            ],
            options={
                'verbose_name': 'Файл с информацией',
                'verbose_name_plural': 'Файлы с информацией',
            },
        ),
        migrations.CreateModel(
            name='Position',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=512, verbose_name='Название')),
                ('level', models.CharField(blank=True, max_length=20, null=True, verbose_name='Карьерный уровень')),
            ],
            options={
                'verbose_name': 'Должность',
                'verbose_name_plural': 'Должности',
            },
        ),
        migrations.CreateModel(
            name='PositionToTargetPosition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='target', to='users.position', verbose_name='Текущая должность')),
                ('target', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.position', verbose_name='Целевая должность')),
            ],
        ),
        migrations.CreateModel(
            name='PositionToCompanyUnit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_unit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.companyunit', verbose_name='Подразделение')),
                ('position', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.position', verbose_name='Должность')),
            ],
        ),
        migrations.AddField(
            model_name='position',
            name='company_units',
            field=models.ManyToManyField(related_name='positions', through='users.PositionToCompanyUnit', to='users.CompanyUnit', verbose_name='Подразделения'),
        ),
        migrations.AddField(
            model_name='position',
            name='targets',
            field=models.ManyToManyField(related_name='previous', through='users.PositionToTargetPosition', to='users.Position', verbose_name='Целевые должности'),
        ),
    ]
