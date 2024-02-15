from typing import Dict

from django.db import models


class BaseTextChoices(models.TextChoices):

    @property
    def slug_name_dict(self) -> Dict[str, str]:
        """Возвращает словарь вида {'slug': choice.value, 'name': choice.label}."""

        return {
            'slug': self.value,
            'name': self.label
        }


class CareerTypeChoices(models.TextChoices):
    EXPERT = 'expert', 'Экспертная'
    MANAGER = 'manager', 'Управленческая'
    PROJECT = 'project', 'Проектная'


class CareerInfoChoices(models.TextChoices):
    """Список query параметров slug - разделов для модели Section"""
    EXPERT_VACANCIES_LIST = 'expert_vacancies_list', 'Экспертный тип карьеры. Список вакансий'
    MANAGER_VACANCIES_LIST = 'manager_vacancies_list', 'Управленческий тип карьеры. Список вакансий'
    VACANCY_DESCRIPTION = 'vacancy_description', 'Описание вакансии'
    SUBMITTED_REQUESTS = 'submitted_requests', 'Отправленные заявки'
    INCOMING_REQUESTS = 'incoming_requests', 'Входящие заявки'
    MY_VACANCIES_BOSS = 'my_vacancies_boss', 'Руководитель. Мои вакансии'
    VACANCIES_HR = 'vacancies_hr', 'HR. Вакансии'
    HEAD_HR = 'head_hr_vacancies_list', 'Head HR. Список вакансий'


CAREER_TYPE_MAP = {
    CareerTypeChoices.EXPERT.value: 'П',  # Проф. должности содержат П (П1, МП2, ТП3 ...)
    CareerTypeChoices.MANAGER.value: 'Р'  # Руководящие должности начинаются с Р
}
