import logging
from typing import List, Union

from django.apps import apps
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as StockUserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from app.models import TimestampedModel
from company.models import Unit
from core.utils import get_employee_data
from vacancies.enums import VacancyRateChoices

logger = logging.getLogger(__name__)


class UserQuerySet(models.QuerySet):
    def with_user_full_name(self):
        """Добавляет ФИО пользователя в queryset.
        Чтобы не было конфликта с property full_name - названо user_full_name.
        """
        return self.annotate(
            user_full_name=models.functions.Concat(
                models.F('last_name'), models.Value(' '),
                models.F('first_name'), models.Value(' '),
                models.F('middle_name'), output_field=models.CharField()
            )
        )

    def with_is_unit_manager(self):
        """Добавляет признак - является ли пользователь руководителем подразделения.
        Чтобы не было конфликта с пермишеном и флагом is_manager - названо is_unit_manager.
        """
        return self.annotate(is_unit_manager=models.Exists(Unit.objects.filter(manager=models.OuterRef('pk'))))


class UserManager(StockUserManager, models.Manager.from_queryset(UserQuerySet)):
    def _create_user(self, personnel_number, email, password, **extra_fields):
        if not personnel_number:
            raise ValueError("The given personnel_number must be set")
        email = self.normalize_email(email)
        GlobalUserModel = apps.get_model(
            self.model._meta.app_label, self.model._meta.object_name
        )
        personnel_number = GlobalUserModel.normalize_username(personnel_number)
        user = self.model(personnel_number=personnel_number, email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, personnel_number, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(personnel_number, email, password, **extra_fields)

    def create_superuser(self, personnel_number, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(personnel_number, email, password, **extra_fields)


class User(AbstractUser, TimestampedModel):
    objects = UserManager()
    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        _("username"),
        max_length=150,
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        validators=[username_validator],
    )
    middle_name = models.CharField('Отчество', max_length=150, blank=True)
    personnel_number = models.CharField(
        'Табельный номер',
        max_length=15,
        unique=True,
        error_messages={
            "unique": "Пользователь с таким табельным номером уже существует",
        },
    )
    image_url = models.URLField(
        max_length=200,
        verbose_name='Ссылка на фото пользователя',
        blank=True,
        null=True
    )
    custom_image_url = models.URLField(
        max_length=200,
        verbose_name='Ссылка на фото внутри сервиса',
        blank=True,
        help_text='Кастомное фото для сервиса. Если проставлено - будет использоваться внутри сервиса.'
    )
    hired_at = models.DateField('Дата устройства', default=timezone.now)
    fired_at = models.DateField('Дата увольнения', null=True, blank=True)
    is_decret = models.BooleanField('Декрет', default=False)
    position = models.ForeignKey(
        'company.Position',
        verbose_name='Должность',
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name='users'
    )
    manager = models.ForeignKey(
        'self',
        verbose_name='Руководитель',
        blank=True,
        null=True,
        related_name='subordinates',
        on_delete=models.PROTECT
    )
    unit = models.ForeignKey(
        'company.Unit',
        verbose_name='Подразделение',
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name='users'
    )
    city = models.ForeignKey(
        'company.City',
        verbose_name='Город',
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name='users'
    )

    USERNAME_FIELD = "personnel_number"

    class Meta:
        permissions = (
            ('is_manager', 'This user is manager'),
            ('is_hr', 'This user is HR'),
            ('is_head_hr', 'This user is head of HR')
        )
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.full_name or self.personnel_number

    @property
    def full_name(self):
        return ' '.join(f'{self.last_name} {self.first_name} {self.middle_name}'.split())

    @property
    def short_name(self):
        return ' '.join(f'{self.first_name} {self.last_name}'.split())

    @cached_property
    def manager_level(self) -> str:
        data = get_employee_data(url='manager_level', params={'personnel_number': self.personnel_number})
        if data:
            return data.get('data').get('manager_level')
        return ''

    @cached_property
    def get_position(self) -> str:
        if self.position:
            return self.position.name
        return ''

    @cached_property
    def top_performer_rate(self) -> str:
        """Возвращает буквенное обозначение оценки Top Performers сотрудника."""
        data = get_employee_data(url='employee/topperformerrate', params={'personnel_number': self.personnel_number})
        if not data:
            return ''
        rate = data.get('data').get('category')
        # Если у сотрудника не проставлен рейт - возвращаем оценку C
        return rate if rate else VacancyRateChoices.C

    @cached_property
    def department_hierarchy(self) -> List[Unit]:
        """Возвращает иерархию подразделений, в которые входит сотрудник.
        Первый элемент - департамент сотрудника, далее идут родители.
        """
        data = get_employee_data(url='departments', params={'pn': self.personnel_number})
        return Unit.load_from_chain(data)[::-1]

    @property
    def department(self) -> Union[Unit, None]:
        """Возвращает направление сотрудника (финансы, тех.блок и тд).
        Направление - это подразделение 2-го уровня в структуре (технический блок, финансы, управление данными)
        """
        hierarchy = self.department_hierarchy
        if hierarchy and len(hierarchy) >= 3:
            return hierarchy[-3]
        return None

    @property
    def image(self):
        return self.custom_image_url or self.image_url

    def update_from_employee(self) -> str:
        """
        Обновляет данные о пользователе с сервиса employee.
        В случае наличия ошибки, возвращает ее в текстовом виде.
        """
        employee_data = get_employee_data(url='employee', params={"pn": self.personnel_number})
        error = ''
        if employee_data:
            from users.serializers import UserEmployeeSerializer
            serializer = UserEmployeeSerializer(data=employee_data['data'], instance=self)
            if serializer.is_valid():
                serializer.save()
            else:
                error = """Не удалось обновить данные по сотруднику {personnel_number}\n
                        Ошибки валидации: {errors}.\n
                        Полученные данные: {employee_data}""".format(
                    personnel_number=self.personnel_number,
                    errors=serializer.errors,
                    employee_data=employee_data["data"]
                )
                logger.error(error)
        else:
            error = f'Данные по {self.personnel_number} не найдены.'
            logger.error(error)
        return error
