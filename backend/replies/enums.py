from django.db import models

from core.enums import BaseTextChoices


class ReplyStatusChoices(BaseTextChoices):
    PENDING = 'pending', 'На согласовании'
    APPROVED = 'approved', 'Согласована'
    HIRED = 'hired', 'Принят'
    REJECTED = 'rejected', 'Отклонена'
    INTERVIEW = 'interview', 'Собеседование'
    CANCELED = 'canceled', 'Отозвана'
    CLOSED = 'closed', 'Закрыта'


class StepStateChoices(models.TextChoices):
    EXPECTED = 'expected', 'Ожидает'
    ACTIVE = 'active', 'Активен'
    HIDDEN = 'hidden', 'Скрыт'
    END = 'end', 'Завершен'
    STOP = 'stop', 'Процесс остановлен'


class StepRoleChoices(models.TextChoices):
    BOSS = 'boss', 'Текущий руководитель'
    NEW_BOSS = 'new_boss', 'Будущий руководитель'
    USER = 'user', 'Соискатель'


class StepResolutionChoices(models.TextChoices):
    APPROVED = 'approved', 'Согласована'
    REJECTED = 'rejected', 'Отклонена'
    INTERVIEW = 'interview', 'Собеседование'


class TitleStateChoices(models.TextChoices):
    AGREEMENT = 'agreement', 'Согласование'
    INTERVIEW = 'interview', 'Собеседование'
    HIRED = 'hired', 'Принят'


class ExperienceChoices(BaseTextChoices):
    FROM_0_TO_3_MONTH = 'from_0_to_3_month', 'От 0 до 3 месяцев'
    FROM_3_TO_6_MONTH = 'from_3_to_6_month', 'От 3 до 6 месяцев'
    FROM_6_TO_9_MONTH = 'from_6_to_9_month', 'От 6 до 9 месяцев'
    FROM_9_TO_12_MONTH = 'from_9_to_12_month', 'От 9 до 12 месяцев'
    MORE_THEN_YEAR = 'more_then_year', 'От года и больше'
