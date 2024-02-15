from django.core import validators
from django.db import models

from app.models import TimestampedModel
from core.enums import CareerInfoChoices, CareerTypeChoices
from core.utils import file_path


class BaseCard(models.Model):
    title = models.CharField(
        verbose_name='Заголовок',
        max_length=100
    )
    description = models.TextField(
        verbose_name='Описание',
        blank=True
    )
    url = models.URLField(
        verbose_name='Адрес ссылки',
        max_length=1000,
        null=True,
        blank=True
    )
    url_display = models.CharField(
        verbose_name='Текст ссылки',
        max_length=250,
        null=True,
        blank=True
    )
    active = models.BooleanField(
        verbose_name='Активна',
        null=False,
        default=True
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f"Карточка: {self.title}"


class CareerType(models.Model):
    slug = models.SlugField(
        primary_key=True,
        verbose_name='Тип карьеры',
        max_length=50,
        null=False,
        blank=False,
        choices=CareerTypeChoices.choices
    )

    class Meta:
        verbose_name = 'Тип карьеры'
        verbose_name_plural = 'Типы карьеры'

    def __str__(self):
        return f"Тип карьеры: {self.slug}"


class Info(models.Model):
    title = models.CharField('Заголовок', max_length=500)
    description = models.TextField('Описание')
    priority = models.PositiveSmallIntegerField(
        verbose_name='Приоритет',
        validators=(validators.MaxValueValidator(10), validators.MinValueValidator(1)),
        default=10,
        help_text='Информация с наименьшим значением будет выдаваться первой. Диапазон значений: [1;10]',
    )
    sections = models.ManyToManyField(
        'Section',
        verbose_name='Разделы',
        through='InfoToSection',
        related_name='info')

    class Meta:
        verbose_name = 'Частый вопрос'
        verbose_name_plural = 'Частые вопросы'

    def __str__(self):
        return f'Вопрос: {self.title}'


class Section(models.Model):
    slug = models.SlugField(
        primary_key=True,
        max_length=70,
        blank=False,
        null=False,
        verbose_name='Раздел',
        choices=CareerInfoChoices.choices
    )

    class Meta:
        verbose_name = 'Раздел'
        verbose_name_plural = 'Разделы'

    def __str__(self):
        return self.get_slug_display()


class InfoToSection(models.Model):
    info = models.ForeignKey('Info', on_delete=models.CASCADE, verbose_name='Частый вопрос')
    section = models.ForeignKey('Section', on_delete=models.CASCADE, verbose_name='Раздел')


class CoreFile(TimestampedModel):
    """Модель для загрузки любых файлов."""

    file = models.FileField(
        verbose_name='Файл',
        upload_to=file_path
    )

    class Meta:
        verbose_name = 'Файл'
        verbose_name_plural = 'Файлы'

    def __str__(self):
        return self.file.name
