import logging
import time
from typing import Dict, List, Optional, Union

from django.conf import settings
from django.db import models
from django.db.models import Count, Q
from mptt.models import MPTTModel, TreeForeignKey, TreeManager
from mptt.querysets import TreeQuerySet

from app.models import IsActiveMixin, TimestampedModel
from company.enums import SelectionTypeChoices
from core.utils import file_path, get_employee_data
from vacancies.enums import VacancyStatusChoices

logger = logging.getLogger(__name__)


class City(models.Model):
    name = models.CharField(
        'Название', max_length=150, unique=True,
        error_messages={
            "unique": "Такой город уже существует",
        },
    )
    sap_id = models.CharField("Id города sap", max_length=150, null=True)

    class Meta:
        verbose_name = 'Город'
        verbose_name_plural = 'Города'

    def __str__(self):
        return self.name


class Office(models.Model):
    """Адреса офисов"""
    city = models.ForeignKey(City, on_delete=models.PROTECT, related_name='offices')
    sap_city_id = models.CharField("Id города sap", max_length=150)
    sap_id = models.CharField("Id код офиса", max_length=150)
    sap_company_id = models.CharField("Id компании sap", max_length=150, blank=True)
    company = models.CharField("Название компании", max_length=250, blank=True)
    sap_branch_id = models.CharField("Id код филиала", max_length=150, blank=True)
    branch = models.CharField("Название филиала", max_length=250, blank=True)
    street = models.CharField('Название улицы', max_length=240, blank=True)
    building = models.CharField('Здание', max_length=250, blank=True)

    class Meta:
        verbose_name = 'Офис'
        verbose_name_plural = 'Офисы'

    def __str__(self):
        return f'Офис {self.city.name} {self.street} {self.building}'


class UnitQueryset(TreeQuerySet):
    def departments(self):
        """Направления (тех.блок, финансы и тп).
        lvl 0 - Филиалы и дочерние компании ПАО 'МегаФон'
        lvl 1 - Тех. блок, финансы, Мегатех и тд.
        lvl 2 - ...
        """
        return self.filter(level=1)


class UnitManager(TreeManager):
    def deactivate_not_company(self):
        return self.get_queryset_descendants(
            self.root_nodes().exclude(code=settings.ROOT_DEPARTMENT_CODE),
            include_self=True
        ).filter(
            is_active=True
        ).update(is_active=False)


class Unit(MPTTModel, IsActiveMixin):
    objects = UnitManager.from_queryset(UnitQueryset)()

    name = models.CharField(verbose_name='Название', max_length=512)
    code = models.CharField(
        verbose_name='Код подразделения',
        max_length=20,
        unique=True,
        error_messages={
            "unique": "Подразделение с таким кодом уже существует",
        },
    )
    parent = TreeForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    manager = models.ForeignKey(
        'users.User',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name='Руководитель',
        related_name='subordinate_units'
    )

    class Meta:
        verbose_name = 'Подразделение'
        verbose_name_plural = 'Подразделения'

    def __str__(self):
        return f'Подразделение {self.name}'

    @property
    def chain(self) -> TreeQuerySet:
        """Цепочка подразделений."""
        return self.get_ancestors(include_self=True)

    @property
    def users_and_managers(self) -> models.QuerySet:
        """Список сотрудников подразделения + вышестоящие руководители.
        Берем сотрудников депатрамента + руководителей родительских подразделений до level=2.
        Отдаем сначала рук-лей, потом сотрудников депатрамента в алфавитном порядке.
        """
        from users.models import User
        return self.users.all().with_user_full_name().with_is_unit_manager().union(
            User.objects.with_user_full_name().with_is_unit_manager().filter(
                subordinate_units__in=self.get_ancestors().filter(level__gt=2)
            )
        ).order_by('-is_unit_manager', 'user_full_name')

    @staticmethod
    def load_from_chain(data: dict) -> List['Unit']:
        """Создает подразделения по data из employee.
        data - словарь с цепочкой подразделений из employee вида {'data': [{unit_1}, ...]}
        Возвращает иерархию департаментов, где в начале стоит родительский департамент, дочерние в конце.
        """
        if not data:
            logger.error('No response from employee. Returning []')
            return []

        units = list(reversed([{**d, 'id': str(d['id'])} for d in data.get('data')]))
        parent = None
        for index, unit in enumerate(units):
            unit = Unit.objects.get_or_create(name=unit['name'], code=unit['id'], parent=parent)[0]
            units[index] = parent = unit
        return units

    def get_num_vacancies_from_descendants(self) -> int:
        """Общее количество вакансий со всех дочерних подразделений
        """
        return self.get_descendants(include_self=True).aggregate(
            num=Count('vacancies', filter=Q(vacancies__status=VacancyStatusChoices.PUBLISHED))
        )['num']


class Position(IsActiveMixin):
    name = models.CharField(verbose_name='Название', max_length=512)
    unit = models.ForeignKey(
        'Unit', verbose_name='Подразделение', related_name='positions', on_delete=models.CASCADE
    )
    code = models.CharField(verbose_name='Id штатной должности', max_length=512, unique=True)
    targets = models.ManyToManyField(
        'self', verbose_name='Целевые должности',
        through='PositionToTargetPosition', symmetrical=False, related_name='previous'
    )
    # Карьерный уровень состоит из 2 символов.
    # Первый - карьерная группа должности (П - для "Профессионалы", Р - для "Руководители)
    # Второй - число, обозначающее уровень (напр. П3, Р4 и тп)
    level = models.CharField(verbose_name='Карьерный уровень', max_length=20, blank=True, null=True)
    selection_type = models.CharField(
        verbose_name='Тип подбора',
        choices=SelectionTypeChoices.choices,
        default=SelectionTypeChoices.PROFESSIONAL,
        max_length=217
    )

    class Meta:
        verbose_name = 'Должность'
        verbose_name_plural = 'Должности'

    def __str__(self):
        return f'Должность {self.name}'

    @staticmethod
    def get_levels_dict(levels: List[str]) -> Dict[str, List[int]]:
        """Собираем уровни в словарь вида {'alpha_prefix': [num_suffix1, num_suffix2, ...], ...}
        НЕ УЧИТЫВАЕТ УРОВНИ БОЛЬШЕ 9!
        Пример:
        levels = ['П2', 'П3', 'П4', 'МП2', 'МП3'] =>
        => levels_dict = {'МП': [2, 3], 'П': [2, 3, 4]}
        """

        levels_dict = {}
        # TODO НЕ УЧИТЫВАЕТ УРОВНИ БОЛЬШЕ 9, потенциальная доработка, хотя пока нет уровней выше 9
        # Сортируем уровни по числовому значению, чтобы списки в levels_dict.values() были отсортированы по возрастанию
        # а также убираем дубли в списке
        levels = list(set(levels))
        levels.sort(key=lambda lvl: lvl[-1])
        for level in levels:
            # TODO НЕ УЧИТЫВАЕТ УРОВНИ БОЛЬШЕ 9, потенциальная доработка, хотя пока нет уровней выше 9
            alpha_part = level[:-1]
            num_part = int(level[-1])
            if alpha_part not in levels_dict:
                levels_dict[alpha_part] = []
            levels_dict[alpha_part].append(num_part)
        return levels_dict


class PositionToTargetPosition(models.Model):
    position = models.ForeignKey(
        'Position', on_delete=models.CASCADE, verbose_name='Текущая должность', related_name='target'
    )
    target = models.ForeignKey('Position', on_delete=models.CASCADE, verbose_name='Целевая должность')


class InfoFile(TimestampedModel):
    """Модель для загрузки файлов csv и наполнения базы данными."""

    file = models.FileField(
        verbose_name='Файл',
        upload_to=file_path
    )

    class Meta:
        verbose_name = 'Файл с информацией'
        verbose_name_plural = 'Файлы с информацией'

    def __str__(self):
        return self.file.name

    def connect_position_to_unit(
            self, position: str, level: str, code: Optional[Union[int, str]]
    ) -> Position:
        """Связывает должность с подразделением.
        :param position: Должность
        :param level: Карьерный уровень должности
        :param code: Код подразделения

        :return Position: Возвращает объект созданной должности
        """
        code = str(code)
        # Ищем подразделение по коду, если не нашли - идем на эмплои
        if not Unit.objects.filter(code=code).exists():
            data = get_employee_data('departments', params={'department_id': code})
            Unit.load_from_chain(data)

        unit = Unit.objects.get(code=code)

        position = Position.objects.get_or_create(name=position, level=level)[0]
        position.units.add(unit)

        return position

    def parse_positions_and_units(self):
        """Парсер csv файла со списком должностей и подразделений.
        Должность|Код подразделения|Карьерный уровень начальной должности|...
        ...Целевая должность|Код подразделения|Карьерный уровень целевой должности|
        """
        start = time.time()
        with self.file.open() as file:
            logging.info(f'Load info from {self.file.name}.')
            line_number = 1
            file.readline()  # Пропускаем первую строку с названием полей

            for line in file.readlines():
                line_number += 1
                logger.info(f'Importing {line_number} line. Time: {time.time() - start}')
                line = line.decode('utf-8').strip('\n').split('|')
                position, code, level = line[0], line[1], line[2]
                target_position, target_code, target_level = line[3], line[4], line[5]
                try:
                    position = self.connect_position_to_unit(position, level, code)
                    target_position = self.connect_position_to_unit(target_position, target_level, target_code)
                    PositionToTargetPosition.objects.get_or_create(position=position, target=target_position)
                except Exception as e:
                    logger.error(f'Error while loading file on line {line_number}: {e}')
