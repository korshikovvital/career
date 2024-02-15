from __future__ import annotations

from collections import defaultdict

from django.conf import settings
from django.core import validators
from django.db import models
from django.db.models import Count

from app.models import TimestampedModel
from app.utils import prepare_and_send_templated_email
from core.enums import CareerTypeChoices
from core.models import BaseCard, CareerType
from core.utils import file_path
from main.enums import CareerTypeCardChoices


class CareerTypeCard(BaseCard):
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to=file_path,
        blank=False,
        null=False
    )
    type = models.CharField(
        max_length=50,
        verbose_name='Тип карьеры',
        choices=CareerTypeCardChoices.choices,
        unique=True,
        error_messages={
            "unique": "Такой тип карьеры уже существует",
        },
    )
    priority = models.PositiveSmallIntegerField(
        verbose_name='Приоритет',
        default=10,
        help_text="Карточка с наименьшим значением будет выдаваться первой"
    )

    class Meta:
        verbose_name = 'Карточка "Тип карьеры"'
        verbose_name_plural = 'Карточки "Тип карьеры"'


class InterestingCard(BaseCard):
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to=file_path,
        blank=False,
        null=False
    )
    priority = models.PositiveSmallIntegerField(
        verbose_name='Приоритет',
        default=10,
        help_text="Карточка с наименьшим значением будет выдаваться первой"
    )

    class Meta:
        verbose_name = 'Карточка "Интересное для тебя"'
        verbose_name_plural = 'Карточки "Интересное для тебя"'


class EmployeeCard(BaseCard, TimestampedModel):
    user = models.OneToOneField(
        'users.User',
        on_delete=models.PROTECT,
        related_name='employee_card',
        verbose_name='Пользователь',
        null=False,
        blank=False
    )

    class Meta:
        verbose_name = 'Карточка "Карьера и кофе"'
        verbose_name_plural = 'Карточки "Карьера и кофе"'


class BannerImage(models.Model):
    banner = models.ForeignKey(
        'Banner',
        on_delete=models.CASCADE,
        related_name='banner_images',
        verbose_name='Баннер',
        null=False,
        blank=False
    )
    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE,
        related_name='banner_image',
        verbose_name='Пользователь',
    )

    class Meta:
        verbose_name = 'Изображение сотрудника в шапке'
        verbose_name_plural = 'Изображения сотрудников в шапке'


class Banner(models.Model):
    title = models.CharField(
        verbose_name='Заголовок баннера',
        max_length=200,
        blank=False,
        null=False,
    )
    text = models.CharField(
        verbose_name='Текст баннера',
        max_length=1000,
        blank=False,
        null=False,
    )

    class Meta:
        verbose_name = 'Баннер в шапке страницы'
        verbose_name_plural = 'Баннеры в шапке страницы'

    def __str__(self):
        return self.title


class Question(models.Model):
    text = models.CharField(
        verbose_name='Текст вопроса',
        max_length=500,
        blank=False,
        null=False
    )
    career_type = models.ForeignKey(
        'core.CareerType',
        on_delete=models.PROTECT,
        verbose_name='Категория положительного ответа на текущий вопрос',
        related_name='questions',
        help_text='К какому карьерному типу предпочтительнее будет определить сотрудника при положительном ответе на '
                  'текущий вопрос'
    )
    poll = models.ForeignKey(
        'Poll',
        on_delete=models.PROTECT,
        verbose_name='Тест',
        related_name='questions',
        null=True,
        blank=True
    )
    priority = models.PositiveSmallIntegerField(
        verbose_name='Приоритет',
        validators=(validators.MaxValueValidator(100), validators.MinValueValidator(1)),
        default=100,
        help_text='Вопрос с наименьшим значением будет выдаваться первым. Диапазон значений: [1;100]',
    )

    class Meta:
        verbose_name = 'Вопрос для теста'
        verbose_name_plural = 'Вопросы для теста'
        ordering = ('priority',)


class Poll(models.Model):
    title = models.CharField(
        'Заголовок в баннере теста',
        max_length=255,
    )
    text = models.CharField(
        'Текст в баннере теста',
        max_length=1024,
        blank=True
    )

    class Meta:
        verbose_name = "Тест"
        verbose_name_plural = "Тесты"

    def __str__(self):
        return f'{self.title}'


class PollResult(models.Model):
    text = models.CharField(
        'Текст результата',
        max_length=700,
        blank=False,
        null=False
    )
    career_types = models.ManyToManyField(
        'core.CareerType',
        through='PollResultToCareerType',
        verbose_name='Типы карьеры',
        related_name='poll_results',
        help_text='К каким карьерным типам относится текущий результат',
    )

    class Meta:
        verbose_name = "Результат теста"
        verbose_name_plural = "Результаты теста"

    @classmethod
    def calculate_results(cls, answers: list[dict]) -> PollResult:

        # Формируем словарь с карьерными типами
        count_career_type = {
            career_type: 0 for career_type, _ in CareerTypeChoices.choices
        }
        # Забираем только те вопросы, на которые ответили "Да"
        questions = Question.objects.select_related("career_type").filter(
            id__in=[answer["question_id"] for answer in answers if answer["answer"]]
        )
        # Считаем количество выбранных карьерных типов
        for question in questions:
            count_career_type[question.career_type.slug] += 1
        # Формируем словарь, в котором ключи - количество выбранных карьерных типов, а значения - сет из набора
        # соответствующих типов. Необходимо для того, чтобы определить максимально значимые карьерные типы
        final_count_career_type = defaultdict(set)
        for key, value in count_career_type.items():
            final_count_career_type[value].add(key)

        max_counts = max(final_count_career_type.keys())

        if max_counts == 0:
            return PollResult.objects.filter(career_types__isnull=True).last()

        career_types = list(final_count_career_type[max_counts])

        # https://groups.google.com/g/django-users/c/X9TCSrBn57Y
        # Ищем такие результаты, которые будут соответствовать выбранным карьерным типам
        poll_result = PollResult.objects.filter(
            career_types__in=career_types
        ).annotate(
            num_types=Count('career_types')
        ).filter(
            num_types=len(career_types)
        ).exclude(
            career_types__in=CareerType.objects.exclude(
                slug__in=career_types)
        ).last()
        return poll_result


class PollResultToCareerType(models.Model):
    poll_result = models.ForeignKey('PollResult', on_delete=models.CASCADE, verbose_name='Ответ')
    type = models.ForeignKey('core.CareerType', on_delete=models.CASCADE, verbose_name='Тип карьеры')


class Invitation(TimestampedModel):
    sender = models.ForeignKey(
        'users.User', on_delete=models.CASCADE, verbose_name='Пригласивший', related_name='invitation_sender'
    )
    recipient = models.ForeignKey(
        'users.User', on_delete=models.CASCADE, verbose_name='Приглашенный', related_name='invitation_recipient'
    )

    class Meta:
        verbose_name = "Приглашение на встречу"
        verbose_name_plural = "Приглашения на встречи"

    def send_email(self):
        context = {
            'main_site_link': settings.MAIN_SITE_LINK,
            'sender': self.sender,
            'recipient': self.recipient
        }
        prepare_and_send_templated_email(
            [self.recipient.email],
            'email/main/invitation_recipient',
            'Твоя история успеха вдохновляет',
            context
        )
        prepare_and_send_templated_email(
            [self.sender.email],
            'email/main/invitation_sender',
            'Твоё приглашение на кофе отправлено',
            context
        )
