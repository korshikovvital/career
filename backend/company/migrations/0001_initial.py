# Generated by Django 3.2.15 on 2022-10-28 12:09

import django.db.models.deletion
import mptt.fields
from django.db import migrations, models

import core.utils


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='City',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(error_messages={'unique': 'Такой город уже существует'}, max_length=150, unique=True, verbose_name='Название')),
            ],
            options={
                'verbose_name': 'Город',
                'verbose_name_plural': 'Города',
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
            name='Unit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=512, verbose_name='Название')),
                ('code', models.CharField(blank=True, max_length=20, null=True, verbose_name='Код подразделения')),
                ('lft', models.PositiveIntegerField(editable=False)),
                ('rght', models.PositiveIntegerField(editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(editable=False)),
                ('parent', mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='company.unit')),
            ],
            options={
                'verbose_name': 'Подразделение',
                'verbose_name_plural': 'Подразделения',
            },
        ),
        migrations.CreateModel(
            name='PositionToUnit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='company.position', verbose_name='Должность')),
                ('unit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='company.unit', verbose_name='Подразделение')),
            ],
        ),
        migrations.CreateModel(
            name='PositionToTargetPosition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='target', to='company.position', verbose_name='Текущая должность')),
                ('target', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='company.position', verbose_name='Целевая должность')),
            ],
        ),
        migrations.AddField(
            model_name='position',
            name='targets',
            field=models.ManyToManyField(related_name='previous', through='company.PositionToTargetPosition', to='company.Position', verbose_name='Целевые должности'),
        ),
        migrations.AddField(
            model_name='position',
            name='units',
            field=models.ManyToManyField(related_name='positions', through='company.PositionToUnit', to='company.Unit', verbose_name='Подразделения'),
        ),
    ]