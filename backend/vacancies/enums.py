from django.db import models

from core.enums import BaseTextChoices


class VacancyStatusChoices(BaseTextChoices):
    PUBLISHED = 'published', 'Опубликована'
    # Статус проставляется, если по одной из заявок на вакансию имеется статус "Принят".
    # Вакансия закрыта автоматически по истечению срока или рекрутером.
    CLOSED = 'closed', 'Закрыта'
    MODERATION = 'moderation', 'На модерации'
    CANCELED = 'canceled', 'Аннулирована'


class VacancyTypeChoices(models.TextChoices):
    AVAILABLE = 'available', 'Доступные'
    GROWTH = 'growth', 'На вырост'
    OTHER = 'other', 'Другие направления'


class VacancyRateChoices(models.TextChoices):
    A = 'A'
    B = 'B'
    C = 'C'
    D = 'D'
    E = 'E'


class QuestionType(models.TextChoices):
    OPEN = 'open', 'Открытый'
    MULTI = 'multi', 'Несколько ответов'
    SINGLE = 'single', 'Один ответ'


class VacancyStateChoices(BaseTextChoices):
    """Статусы для описания вакансии."""
    TEST_FAILED = 'test_failed', 'Тестирование не пройдено'
    REPLIED = 'replied', 'Заявка отправлена'
    CANT_REPLY = 'cant_reply', 'Нельзя откликнуться'
    REPLY = 'reply', 'Откликнуться'
    GROWTH_VACANCY = 'growth_vacancy', 'Вакансия на вырост'
    RATE_MISMATCH = 'rate_mismatch', 'Несоответствие уровня'


class VacancyRoleChoices(models.TextChoices):
    MANAGER = 'manager'  # Вакансии для текущего рук-ля
    HR = 'hr'  # Вакансии для рекрутеров
    HEAD_HR = 'head_hr'  # Руководитель рекрутеров


class VacancyOwnerChoices(models.TextChoices):
    ME = 'me'
    OTHER = 'other'


ROLE_TO_VACANCY_FILTERS = {
    VacancyRoleChoices.MANAGER: VacancyStatusChoices.values,
    VacancyRoleChoices.HR: VacancyStatusChoices.values,
    VacancyRoleChoices.HEAD_HR: VacancyStatusChoices.values
}
