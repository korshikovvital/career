import logging
from datetime import date

from django.conf import settings
from django.core import validators
from django.db import models
from django.db.models import Q
from django.db.models.functions import Now
from django.utils import timezone
from mdeditor.fields import MDTextField

from app.models import TimestampedModel
from company.enums import SelectionTypeChoices
from company.models import Position
from core.utils import file_path
from replies.enums import ReplyStatusChoices, StepStateChoices
from replies.models import Step
from users.models import User
from vacancies.enums import QuestionType, VacancyStatusChoices, VacancyTypeChoices

logger = logging.getLogger(__name__)


class Vacancy(TimestampedModel):
    title = models.CharField(
        verbose_name='Название вакансии',
        max_length=512
    )
    manager = models.ForeignKey(
        'users.User',
        verbose_name='Руководитель',
        on_delete=models.SET_NULL,
        null=True,
        related_name='vacancies'
    )
    images = models.ManyToManyField(
        'Image',
        verbose_name='Фото офиса',
        through='VacancyToImage',
        related_name='vacancies'
    )
    sap_id = models.CharField(
        "Id sap",
        max_length=150,
        null=True,
        blank=True,
    )
    is_referral = models.BooleanField(
        verbose_name='Реферальная программа',
        default=False
    )
    vacancy_type = models.ForeignKey(
        'VacancyType',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='type_vacancies',
        verbose_name='Тип вакансии')
    reason = models.ForeignKey(
        'Reason',
        on_delete=models.SET_NULL,
        null=True,
        related_name='vacancies',
        verbose_name='Причина открытия вакансии')
    work_experience = models.ForeignKey(
        'WorkExperience',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='experience_vacancies',
        verbose_name='Опыт работы')
    work_contract = models.ForeignKey(
        'WorkContract',
        on_delete=models.SET_NULL,
        null=True,
        related_name='vacancies',
        verbose_name='Вид трудового договора'
    )
    contest_type = models.ForeignKey(
        'ContestType',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='vacancies',
        verbose_name='Вид конкурса'
    )
    release_date = models.DateField(
        'Дата освобождения ставки',
        default=date.today,
        blank=True,
        null=True
    )
    end_date = models.DateField(
        "Дата закрытия вакансии",
        blank=True,
        null=True
    )
    workplace_number = models.CharField(
        'Номер рабочего места',
        max_length=240,
        blank=True,
        null=True
    )
    offices = models.ManyToManyField(
        'company.Office',
        verbose_name='Адреса офисов',
        through='VacancyToOffice',
        related_name='vacancies'
    )
    kpi = models.TextField(
        'Ключевые показатели',
        blank=True,
        null=True
    )
    comment = models.TextField(
        'Комментарий',
        blank=True,
        null=True,
    )
    rate = models.ForeignKey(
        'Rate',
        on_delete=models.CASCADE,
        related_name='vacancies',
        verbose_name='Требуемый уровень'
    )
    duties = models.TextField(
        verbose_name='Задачи',
        help_text='Задачи/должностные обязанности',
        null=True,
    )
    skills = models.TextField(
        verbose_name='Ожидания',
        help_text='Умения/навыки/опыт',
        null=True
    )
    benefits = models.TextField(
        verbose_name='Мы предлагаем',
        help_text='Предлагаемые плюшки (печеньки/кофе/дружный коллектив)',
        null=True,
    )
    position = models.ForeignKey(
        'company.Position',
        verbose_name='Должность',
        on_delete=models.CASCADE,
        null=True,
        related_name='vacancies',
    )
    purpose = models.TextField(
        'Цель должности',
        blank=True,
    )
    # Период отображения знака Горящая вакансия - 1 неделя, по истечении недели значок пропадает.
    hot = models.BooleanField(
        verbose_name='Горящая вакансия',
        default=False
    )
    unit = models.ForeignKey(
        'company.Unit',
        verbose_name='Подразделение',
        on_delete=models.CASCADE,
        blank=False,
        null=True,
        related_name='vacancies'
    )
    recruiter = models.ForeignKey(
        'users.User',
        verbose_name='Рекрутер',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='recruiter_vacancies'
    )
    published_by = models.ForeignKey(
        'users.User',
        verbose_name='Опубликовавший сотрудник',
        on_delete=models.SET_NULL,
        null=True,
        related_name='published_vacancies'
    )
    # Дата публикации проставляется, когда вакансия публикуется - статус меняется с draft на published
    published_at = models.DateField(
        verbose_name='Дата публикации',
        blank=True,
        null=True
    )
    status = models.CharField(
        verbose_name='Статус вакансии',
        choices=VacancyStatusChoices.choices,
        default=VacancyStatusChoices.MODERATION,
        max_length=127
    )
    selection_type = models.CharField(
        verbose_name='Тип подбора',
        choices=SelectionTypeChoices.choices,
        default=SelectionTypeChoices.PROFESSIONAL,
        max_length=217
    )

    # Период отображения вакансии на сервисе - 4 недели.
    # По истечении 4-х недель вакансия закрывается без возможности переоткрытия.
    # Если вакансия горящая, то общий срок её отображения - 5 недель, 1 неделя - горящая, 4 недели - стандартная

    class Meta:
        verbose_name = 'Вакансия'
        verbose_name_plural = 'Вакансии'

    def __str__(self):
        return f'Вакансия {self.title}'

    @staticmethod
    def get_q_for_vacancy_type(type: VacancyTypeChoices, user: User) -> Q:

        current_position = Position.objects.filter(name=user.position).first()
        if not current_position:
            return Q(position=None)
        target_positions = current_position.targets.all()
        target_positions_levels = [position.level for position in target_positions]
        levels_dict = Position.get_levels_dict(target_positions_levels)

        # Получаем уровни для доступных вакансий (первый и второй уровень в каждом буквенном ключе)
        available_positions_levels = []
        for key, value in levels_dict.items():
            rng = 2 if len(value) > 1 else 1
            for i in range(rng):
                # Добавляем числовые значения уровня с индексами (0,1), тк
                # "Хотят не 1 самый низкий уровень, а самый низкий уровень + 1 выше в доступные"
                # Если уровень один, добавляем только его
                available_positions_levels.append(f'{key}{value[i]}')
        # Добавляем текущий уровень, тк мб переход вида П3 -> П3
        available_positions_levels.append(current_position.level)
        q = Q(position__in=target_positions)
        if type == VacancyTypeChoices.AVAILABLE:
            q &= (
                Q(position__level__in=available_positions_levels)
                & Q(unit__in=user.department.get_descendants())
            )
        if type == VacancyTypeChoices.GROWTH:
            q &= (
                ~Q(position__level__in=available_positions_levels)
                & Q(unit__in=user.department.get_descendants())
            )
        if type == VacancyTypeChoices.OTHER:
            # Получаем направления, отличные от направления пользователя
            # Вакансии для других направлений определяются маршрутом перемещения по должностям из файла,
            # те вакансия в другом направлении должна быть в целевой должности для текущей должности пользователя
            # без градации по уровню.
            q &= ~Q(unit__in=user.department.get_descendants())
        return q

    def close(self):
        """
        Устанавливает для вакансии статус ЗАКРЫТА.
        Все отклики, у которых статус СОГЛАСОВАНИЕ или СОБЕСЕДОВАНИЕ, переводим в статус ЗАКРЫТА.
        Все активные шаги этих откликов переводим в состояние END и статус ЗАКРЫТА, а ожидающие в состояние STOP
        """
        self.status = VacancyStatusChoices.CLOSED

        Step.objects.filter(
            reply__vacancy=self,
            reply__status__in=(ReplyStatusChoices.PENDING, ReplyStatusChoices.INTERVIEW),
            state=StepStateChoices.ACTIVE
        ).update(
            state=StepStateChoices.END,
            status=ReplyStatusChoices.CLOSED
        )  # Активные шаги завершаем со статусом ЗАКРЫТА

        Step.objects.filter(
            reply__vacancy=self,
            reply__status__in=(ReplyStatusChoices.PENDING, ReplyStatusChoices.INTERVIEW),
            state=StepStateChoices.EXPECTED
        ).update(
            state=StepStateChoices.STOP
        )  # Все ожидающие шаги переводим в состояние ОСТАНОВЛЕН

        self.replies.filter(status__in=(ReplyStatusChoices.PENDING, ReplyStatusChoices.INTERVIEW)).update(
            status=ReplyStatusChoices.CLOSED
        )  # Меняем статус откликов

        self.save()

    def cancel(self):
        """
        Устанавливает для вакансии статус АННУЛИРОВАНО.
        Все отклики, у которых статус СОГЛАСОВАНИЕ или СОБЕСЕДОВАНИЕ, переводим в статус ЗАКРЫТА.
        Все активные шаги этих откликов переводим в состояние END и статус ЗАКРЫТА, а ожидающие в состояние STOP
        """
        self.status = VacancyStatusChoices.CANCELED

        Step.objects.filter(
            reply__vacancy=self,
            reply__status__in=(ReplyStatusChoices.PENDING, ReplyStatusChoices.INTERVIEW),
            state=StepStateChoices.ACTIVE
        ).update(
            state=StepStateChoices.END,
            status=ReplyStatusChoices.CLOSED
        )  # Активные шаги завершаем со статусом ЗАКРЫТА

        Step.objects.filter(
            reply__vacancy=self,
            reply__status__in=(ReplyStatusChoices.PENDING, ReplyStatusChoices.INTERVIEW),
            state=StepStateChoices.EXPECTED
        ).update(
            state=StepStateChoices.STOP
        )  # Все ожидающие шаги переводим в состояние ОСТАНОВЛЕН

        self.replies.filter(status__in=(ReplyStatusChoices.PENDING, ReplyStatusChoices.INTERVIEW)).update(
            status=ReplyStatusChoices.CLOSED, modified=timezone.now()
        )  # Меняем статус откликов

        self.save()

    @property
    def is_published(self) -> bool:
        """Проверяет, опубликована ли вакансия."""
        return self.status == VacancyStatusChoices.PUBLISHED

    def publish(self):
        """
        Публикация вакансии.
        Устанавливает для вакансии статус ОПУБЛИКОВАНА и проставляет текущую дату в published_at.
        """

        logger.info(f'Publish {self} with id={self.id}')
        self.status = VacancyStatusChoices.PUBLISHED
        self.published_at = Now()
        self.save()


class VacancyToOffice(models.Model):
    vacancy = models.ForeignKey('Vacancy', on_delete=models.CASCADE, verbose_name='Вакансия')
    office = models.ForeignKey('company.Office', on_delete=models.CASCADE, verbose_name="Адрес офиса")
    is_main = models.BooleanField('Является ли офис главным', default=False)


class VacancyToImage(models.Model):
    vacancy = models.ForeignKey('Vacancy', on_delete=models.CASCADE, verbose_name='Вакансия')
    image = models.ForeignKey('Image', on_delete=models.CASCADE, verbose_name='Изображение')


class VacancyReserve(models.Model):
    """Модель для Кадрового резерва."""
    title = models.CharField(verbose_name='Название вакансии', max_length=512)
    direction = models.CharField(verbose_name='Направление', max_length=255)
    requirements = MDTextField(verbose_name='Требования', help_text='Стаж/оценка Top Performers/показатели')
    priority = models.PositiveSmallIntegerField(
        verbose_name='Приоритет',
        validators=(validators.MinValueValidator(1),),
        default=1,
        help_text='Информация с наименьшим значением будет выдаваться первой.',
    )

    class Meta:
        verbose_name = 'Кадровый резерв'
        verbose_name_plural = 'Кадровый резерв'

    def __str__(self):
        return f'Кадровый резерв на вакансию {self.title}'


class Image(models.Model):
    file = models.ImageField(
        verbose_name='Изображение',
        upload_to=file_path,
        blank=False,
        null=False
    )

    class Meta:
        verbose_name = 'Изображение'
        verbose_name_plural = 'Изображения'

    def __str__(self):
        return self.file.name


class PollTemplate(models.Model):
    title = models.CharField(
        verbose_name='Название шаблона для опросника',
        max_length=255
    )

    def __str__(self):
        return f'Шаблон для опросника: {self.title}'

    class Meta:
        verbose_name = 'Шаблон для опросника'
        verbose_name_plural = 'Шаблоны для опросника'


class Question(models.Model):
    text = models.CharField(
        verbose_name='Текст вопроса',
        max_length=512
    )
    type = models.CharField(
        verbose_name='Тип вопроса',
        max_length=64,
        choices=QuestionType.choices
    )
    poll_templates = models.ManyToManyField(
        'PollTemplate',
        through='QuestionToPollTemplate',
        verbose_name='Шаблоны для опросника',
        related_name='questions',
    )
    polls = models.ManyToManyField(
        'Poll',
        through='QuestionToPoll',
        verbose_name='Опросники',
        related_name='questions',
    )
    answers = models.ManyToManyField(
        'Answer',
        through='QuestionToAnswer',
        verbose_name='Ответы',
        related_name='questions'
    )

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = 'Вопрос для опросника'
        verbose_name_plural = 'Вопросы для опросника'


class Answer(models.Model):
    text = models.CharField(
        verbose_name='Текст ответа',
        max_length=512
    )

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = 'Ответ на вопрос для опросника'
        verbose_name_plural = 'Ответы на вопросы для опросника'


class QuestionToAnswer(models.Model):
    question = models.ForeignKey(
        'Question',
        on_delete=models.CASCADE,
        verbose_name='Вопрос'
    )
    answer = models.ForeignKey(
        'Answer',
        on_delete=models.CASCADE,
        verbose_name='Ответ'
    )
    is_correct = models.BooleanField(
        verbose_name='Правильный ли ответ?'
    )


class QuestionToPoll(models.Model):
    question = models.ForeignKey(
        'Question',
        on_delete=models.CASCADE,
        verbose_name='Вопрос'
    )
    poll = models.ForeignKey(
        'Poll',
        on_delete=models.CASCADE,
        verbose_name='Опросник'
    )


class QuestionToPollTemplate(models.Model):
    question = models.ForeignKey(
        'Question',
        on_delete=models.CASCADE,
        verbose_name='Вопрос'
    )
    poll_template = models.ForeignKey(
        'PollTemplate',
        on_delete=models.CASCADE,
        verbose_name='Шаблон опросника'
    )


class UserAnswer(models.Model):
    question = models.ForeignKey(
        'Question',
        on_delete=models.CASCADE,
        related_name='user_answer',
        verbose_name='Вопрос'
    )
    answer = models.ForeignKey(
        'Answer',
        on_delete=models.CASCADE,
        related_name='user_answer',
        verbose_name='Ответ',
        null=True,
        blank=True,
        help_text='Заполняется только для вопросов теста'
    )
    poll = models.ForeignKey(
        'Poll',
        on_delete=models.CASCADE,
        related_name='user_answer',
        verbose_name='Опросник'
    )
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='user_answer',
        verbose_name='Пользователь'
    )
    answer_text = models.TextField(
        verbose_name='Текст ответа',
        blank=True,
        help_text='Заполняется только для открытых вопросов'
    )

    def __str__(self):
        return f'Ответ {self.user}'

    class Meta:
        verbose_name = 'Ответ пользователя'
        verbose_name_plural = 'Ответы пользователя'


class Restrict(models.Model):
    vacancy = models.ForeignKey(
        'Vacancy',
        on_delete=models.CASCADE,
        verbose_name='Вакансия',
        help_text='Вакансия, которую НЕ показывать',
        related_name='restrictions'
    )
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        help_text='Кому не показывать',
        related_name='restrictions'
    )

    def __str__(self):
        return f'{self.vacancy}:{self.user}'

    class Meta:
        verbose_name = 'Ограничение показа вакансии'
        verbose_name_plural = 'Ограничения показа вакансий'


class Poll(models.Model):
    title = models.CharField(
        verbose_name='Название опросника',
        max_length=255
    )
    vacancy = models.ForeignKey(
        'Vacancy',
        on_delete=models.CASCADE,
        verbose_name='Вакансия',
        related_name='polls'
    )

    def __str__(self):
        return f'Опросник: {self.title} {self.vacancy}'

    class Meta:
        verbose_name = 'Опросник'
        verbose_name_plural = 'Опросники'


class Factoid(models.Model):
    file = models.ImageField(
        verbose_name='Фактоид',
        upload_to=file_path,
        blank=False,
        null=False
    )

    class Meta:
        verbose_name = 'Фактоид'
        verbose_name_plural = 'Фактоиды'

    def __str__(self):
        return self.file.name


class Rate(models.Model):
    title = models.CharField('Уровень вакансии', max_length=20, unique=True)

    class Meta:
        verbose_name = 'Уровень вакансии'
        verbose_name_plural = 'Уровни вакансий'

    def __str__(self):
        return self.title


class WorkExperience(models.Model):
    title = models.CharField('Опыт работы', max_length=240)
    sap_id = models.CharField(
        "Id sap",
        max_length=150,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Опыт работы'
        verbose_name_plural = 'Опыт работы'

    def __str__(self):
        return self.title


class VacancyType(models.Model):
    title = models.CharField('Тип вакансии', max_length=240)
    sap_id = models.CharField(
        "Id sap",
        max_length=150,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Тип вакансии'
        verbose_name_plural = 'Типы вакансий'

    def __str__(self):
        return self.title


class WorkContract(models.Model):
    title = models.CharField('Вид трудового договора', max_length=240)
    sap_id = models.CharField(
        "Id sap",
        max_length=150,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Вид трудового договора'
        verbose_name_plural = 'Виды трудового договора'

    def __str__(self):
        return self.title


class ContestTypeManager(models.Manager):
    def get_default(self):
        return self.filter(sap_id=settings.DEFAULT_CONTEST_TYPE_SAP_ID).first()


class ContestType(models.Model):
    objects = ContestTypeManager()

    title = models.CharField('Название конкурса', max_length=240)
    sap_id = models.CharField(
        "Id sap",
        max_length=150,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Вид конкурса'
        verbose_name_plural = 'Виды конкурса'

    def __str__(self):
        return self.title


class Reason(models.Model):
    title = models.CharField('Причина открытия вакансии', max_length=240)
    sap_id = models.CharField(
        "Id sap",
        max_length=150,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = 'Причина открытия вакансии'
        verbose_name_plural = 'Причины открытия вакансии'

    def __str__(self):
        return self.title


class VacancyViewed(models.Model):
    vacancy = models.ForeignKey(
        'Vacancy',
        on_delete=models.CASCADE,
        verbose_name='Вакансия',
        help_text='Просмотренная вакансия',
        related_name='viewed_users'
    )
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        help_text='Кто просмотрел',
        related_name='viewed_vacancies'
    )

    def __str__(self):
        return f'{self.user} просмотрел: {self.vacancy}'

    class Meta:
        verbose_name = 'Просмотренная вакансия'
        verbose_name_plural = 'Просмотренные вакансии'
        constraints = [
            models.UniqueConstraint(fields=['user', 'vacancy'],
                                    name='%(app_label)s_%(class)s_is_one_user_to_view_vacancy')
        ]
