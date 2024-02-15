import datetime

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vacancies', '0017_new_sap_fields_to_vacancy'),
    ]

    operations = [
        migrations.AddField(
            model_name='vacancy',
            name='contest_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='vacancies', to='vacancies.contesttype', verbose_name='Вид конкурса'),
        ),
        migrations.AddField(
            model_name='vacancy',
            name='end_date',
            field=models.DateField(blank=True, null=True, verbose_name='Дата закрытия вакансии'),
        ),
        migrations.AddField(
            model_name='vacancy',
            name='selection_type',
            field=models.CharField(choices=[('mass', 'Mass'), ('professional', 'Professional')], default='professional', max_length=217, verbose_name='Тип подбора'),
        ),
        migrations.AlterField(
            model_name='vacancy',
            name='release_date',
            field=models.DateField(blank=True, default=datetime.date.today, null=True, verbose_name='Дата освобождения ставки'),
        ),
        migrations.AlterField(
            model_name='vacancy',
            name='status',
            field=models.CharField(choices=[('published', 'Опубликована'), ('closed', 'Закрыта'), ('moderation', 'На модерации')], default='moderation', max_length=127, verbose_name='Статус вакансии'),
        ),
        migrations.AddField(
            model_name='vacancytooffice',
            name='is_main',
            field=models.BooleanField(default=False, verbose_name='Является офис главным'),
        ),
    ]
