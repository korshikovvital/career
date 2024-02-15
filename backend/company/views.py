from django.db.models import CharField, Count, F, OuterRef, Q, Subquery, Value
from django.db.models.functions import Concat
from rest_framework import generics

from company.models import City, Office, Position, Unit
from company.serializers import (
    CityExtendSerializer,
    DepartmentSerializer,
    OfficeSerializer,
    PositionSerializer,
    UnitSerializer
)
from core.enums import CAREER_TYPE_MAP
from users.models import User
from users.permissions import IsHeadHR, IsHR, IsManager
from vacancies.enums import VacancyStatusChoices
from vacancies.models import Vacancy


class CompanyCitiesView(generics.ListAPIView):
    """Возвращает города.
    query params:
     - type: фильтрация городов по наличию вакансий по типам (доступные/на вырост/др. направлений)
     - career: фильтрация городов по наличию вакансий по карьерным типам (экспертная, управленческая, проектная)

    Без параметров будут отданы все имеющиеся в базе города.
    """
    serializer_class = CityExtendSerializer

    def get_queryset(self):
        type = self.request.query_params.get('type')
        career = self.request.query_params.get('career')
        unit_code = self.request.query_params.get('unit_code')
        q = Q()
        if type:
            vacancy_q = Vacancy.get_q_for_vacancy_type(type, self.request.user)
            q &= Q(offices__vacancies__in=Vacancy.objects.filter(vacancy_q))
        if career:
            # Используем пробел в качестве дефолтного значения, поскольку
            # в уровнях должностей нет пробела, поэтому фильтрация вернет пустой кверисет
            vacancy_q = Q(position__level__icontains=CAREER_TYPE_MAP.get(career, ' '))
            q &= Q(offices__vacancies__in=Vacancy.objects.filter(vacancy_q))
        if unit_code:
            q &= Q(offices__vacancies__status=VacancyStatusChoices.PUBLISHED)
            if not unit_code == 'all':
                units_ids = Unit.objects.filter(code=unit_code).get_descendants(include_self=True).values_list('id', flat=True)
                q &= Q(offices__vacancies__unit_id__in=units_ids)
        return City.objects.prefetch_related('offices').filter(q).annotate(
            total_vacancies=Count('offices__vacancies', filter=Q(offices__vacancies__status=VacancyStatusChoices.PUBLISHED))
        ).order_by('name')


class CompanyUnitsView(generics.ListAPIView):
    serializer_class = UnitSerializer

    def get_queryset(self):
        """Поиск и цепочка подразделений.
        query - Поисковой запрос (название или код подразделения)
        unit_code - Код департамента для которого отдается цепочка подразделений
        level - Получение департаментов определенного уровня.
        При передаче level=2 получим список направлений (Технический блок и тд).
        При отсутствии параметров - возвращает все департаменты, в которых заведены должности - департаменты,
        загруженные из файла.
        """
        query = self.request.query_params.get('query')
        unit_code = self.request.query_params.get('code')
        level = self.request.query_params.get('level')
        if query:
            return Unit.objects.filter(Q(name__icontains=query) | Q(code=query))
        if unit_code:
            unit_qs = Unit.objects.filter(code=unit_code)
            return unit_qs.first().chain if unit_qs else unit_qs
        if level:
            return Unit.objects.filter(level=int(level))
        return Unit.objects.exclude(positions__isnull=True)


class DepartmentsView(generics.ListAPIView):
    serializer_class = DepartmentSerializer

    def get_queryset(self):
        # Исключаем из выборки департамент сотрудника, чтобы в вакансиях "Другие направления"
        # не отдавался департамент сотрудника и не запрашивались вакансии этого департамента
        user_department_code = self.request.user.department.code

        city_id = self.request.query_params.get('city_id')
        career = self.request.query_params.get('career')

        q = Q()

        if city_id:
            q &= Q(children__vacancies__offices__city__id=city_id)

        if career:
            # Используем пробел в качестве дефолтного значения, поскольку
            # в уровнях должностей нет пробела, поэтому фильтрация вернет пустой кверисет
            q &= Q(children__vacancies__position__level__icontains=CAREER_TYPE_MAP.get(career, ' '))

        q &= ~Q(children__vacancies__status__in=(
            VacancyStatusChoices.MODERATION, VacancyStatusChoices.CLOSED, VacancyStatusChoices.CANCELED
        )
        )

        units = Unit.objects.prefetch_related(
            'vacancies', 'vacancies__position', 'vacancies__offices__city',
        ).departments().filter(q).exclude(code=user_department_code).distinct()

        units_to_return = []

        for unit in units:
            total_vacancies = unit.get_num_vacancies_from_descendants()
            if total_vacancies > 0:
                unit.total_vacancies = total_vacancies
                units_to_return.append(unit)

        return units_to_return


class PositionsView(generics.ListAPIView):
    serializer_class = PositionSerializer

    def get_queryset(self):
        unit_code = self.request.query_params.get('unit_code')
        query = self.request.query_params.get('query')
        sub_query = User.objects.annotate(
            full_name=Concat(
                F('last_name'), Value(' '), F('first_name'), Value(' '), F('middle_name'), output_field=CharField()
            )
        ).filter(position_id=OuterRef('id'))
        qs = Position.objects.select_related('unit').annotate(
            user_full_name=Subquery(sub_query.values('full_name')[:1]),
            user_personnel_number=Subquery(sub_query.values('personnel_number')[:1])
        )
        if unit_code:
            return qs.filter(unit__code=unit_code)
        if query:
            return qs.annotate(
                unit_manager_full_name=Concat(
                    F('unit__manager__last_name'),
                    Value(' '),
                    F('unit__manager__first_name'),
                    Value(' '),
                    F('unit__manager__middle_name'),
                    output_field=CharField()
                )
            ).filter(
                Q(user_full_name__icontains=query) |
                Q(user_personnel_number__icontains=query) |
                Q(unit__manager__personnel_number__icontains=query) |
                Q(unit_manager_full_name__icontains=query) |
                Q(code__icontains=query) |
                Q(name__icontains=query)
            )
        return qs


class OfficesView(generics.ListAPIView):
    serializer_class = OfficeSerializer
    queryset = Office.objects.all()
    permission_classes = (IsHR | IsHeadHR | IsManager,)
