# Generated by Django 3.2.16 on 2023-05-12 10:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('replies', '0006_vacancyreservereply'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reply',
            name='status',
            field=models.CharField(choices=[('pending', 'На согласовании'), ('approved', 'Согласована'), ('hired', 'Принят'), ('rejected', 'Отклонена'), ('interview', 'Собеседование'), ('canceled', 'Отозвана'), ('closed', 'Закрыта')], max_length=100, verbose_name='Статус'),
        ),
        migrations.AlterField(
            model_name='step',
            name='resolution',
            field=models.CharField(blank=True, choices=[('approved', 'Согласована'), ('rejected', 'Отклонена'), ('interview', 'Собеседование')], max_length=100, null=True, verbose_name='Решение'),
        ),
        migrations.AlterField(
            model_name='step',
            name='status',
            field=models.CharField(blank=True, choices=[('pending', 'На согласовании'), ('approved', 'Согласована'), ('hired', 'Принят'), ('rejected', 'Отклонена'), ('interview', 'Собеседование'), ('canceled', 'Отозвана'), ('closed', 'Закрыта')], max_length=100, null=True, verbose_name='Статус'),
        ),
    ]