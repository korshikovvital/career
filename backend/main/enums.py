from django.db import models


class CareerTypeCardChoices(models.TextChoices):
    EXPERT = 'expert', 'Экспертная'
    MANAGER = 'manager', 'Управленческая'
    PROJECT = 'project', 'Проектная'
    VACANCIES = 'vacancies', 'Все вакансии'
