from django.db.models import CharField, Exists, F, OuterRef, Q, Value
from django.db.models.functions import Concat
from rest_framework import generics, serializers
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED

from app import errors
from app.pagination import DataWrappingLimitOffsetPagination
from app.responses import NoContentResponse, NotFoundResponse
from company.models import Unit
from core.enums import CAREER_TYPE_MAP
from core.permissions import ReadOnly
from users.permissions import IsHeadHR, IsHR, IsManager
from vacancies.enums import (
    ROLE_TO_VACANCY_FILTERS,
    VacancyOwnerChoices,
    VacancyRoleChoices,
    VacancyStatusChoices
)
from vacancies.models import (
    Factoid,
    Poll,
    PollTemplate,
    Rate,
    Reason,
    Vacancy,
    VacancyReserve,
    VacancyType,
    VacancyViewed,
    WorkContract,
    WorkExperience
)
from vacancies.permissions import PollViewPermission, VacancyViewPermission
from vacancies.serializers import (
    FactoidSerializer,
    MyVacancySerializer,
    PollRequestSerializer,
    PollResponseSerializer,
    PollTemplateShortInfoSerializer,
    RateSerializer,
    ReasonSerializer,
    VacancyCreateUpdateSerializer,
    VacancyDetailRecruiterUpdateSerializer,
    VacancyPatchRecruiterSerializer,
    VacancyQueryParamSerializer,
    VacancyReserveSerializer,
    VacancySerializer,
    VacancyShortSerializer,
    VacancyStatusUpdateSerializer,
    VacancyTypeSerializer,
    WorkContractSerializer,
    WorkExperienceSerializer
)


class VacanciesListCreateView(generics.ListCreateAPIView):
    """Короткое описание вакансии для карточек с вакансиями."""
    pagination_class = DataWrappingLimitOffsetPagination
    permission_classes = (ReadOnly | IsAdminUser | IsHR | IsHeadHR | IsManager,)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return VacancyCreateUpdateSerializer
        return VacancyShortSerializer

    def create(self, request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data, context=request)
        serializer.is_valid(raise_exception=True)
        vacancy = serializer.save()
        return Response({'vacancy_id': vacancy.id}, status=HTTP_201_CREATED)

    def get_queryset(self):
        query = self.request.query_params.get('query')
        unit_code = self.request.query_params.get('unit_code')  # id подразделения 2 уровня (то, что потомок "ПАО Мегафон")
        type = self.request.query_params.get('type')
        city_id = self.request.query_params.get('city_id')
        career = self.request.query_params.get('career')
        q = Q(status=VacancyStatusChoices.PUBLISHED)
        full_name = Concat(
            F('manager__first_name'), Value(' '), F('manager__last_name'), output_field=CharField()
        )
        if type:
            q &= Vacancy.get_q_for_vacancy_type(type, self.request.user)
        if query:
            title_q = Q(title__icontains=query)
            manager_q = Q(full_name__icontains=query)
            unit_q = Q(unit__name__icontains=query)
            q &= (title_q | manager_q | unit_q)
        if city_id:
            q &= Q(offices__city=city_id)
        if career:
            # Логика отбора уровней: руководящие должности содержат в уровне Р, проф. - П.
            # Используем пробел в качестве дефолтного значения, поскольку
            # в уровнях должностей нет пробела, поэтому фильтрация вернет пустой кверисет
            q &= Q(position__level__icontains=CAREER_TYPE_MAP.get(career, ' '))
        if unit_code:
            units = Unit.objects.filter(code=unit_code).get_descendants()
            q &= Q(unit__in=units)
        return Vacancy.objects.prefetch_related('restrictions', 'replies', 'position').annotate(
            full_name=full_name).filter(q).order_by('-hot', '-published_at', '-id').distinct()


class VacancyView(generics.RetrieveAPIView):
    """Подробное описание|редактирование вакансии.
    Редактировать можно только заявки в драфте.
    """
    permission_classes = [VacancyViewPermission]

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            if 'recruiter_personnel_number' in self.request.data:
                return VacancyDetailRecruiterUpdateSerializer
            if 'status' in self.request.data:
                return VacancyStatusUpdateSerializer
            else:
                return VacancyCreateUpdateSerializer
        return VacancySerializer

    def get_object(self):
        obj = self.get_queryset().get(id=self.kwargs.get('id'))
        self.check_object_permissions(self.request, obj)
        VacancyViewed.objects.get_or_create(user=self.request.user, vacancy=obj)
        return obj

    def get_queryset(self):
        queryset = Vacancy.objects.select_related(
            'unit', 'manager', 'position', 'rate', 'recruiter',
            'vacancy_type', 'reason', 'work_experience', 'work_contract'
        ).prefetch_related('offices')
        serializer = self.get_serializer_class()
        if serializer == VacancyCreateUpdateSerializer:
            # Редактировать можно только заявки в драфте
            return queryset.filter(status__in=(VacancyStatusChoices.MODERATION, VacancyStatusChoices.PUBLISHED))
        return queryset

    def patch(self, request, *args, **kwargs):
        vacancy = self.get_object()
        if vacancy.status == VacancyStatusChoices.CLOSED:
            raise ValidationError(detail=errors.TRY_CHANGE_CLOSED_VACANCY)
        serializer = self.get_serializer(
            vacancy,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return NoContentResponse


class FactoidView(generics.ListAPIView):
    serializer_class = FactoidSerializer

    def get_queryset(self):
        limit = int(self.request.query_params.get('limit', 1000))
        return Factoid.objects.order_by('?')[:limit]


class PollView(generics.CreateAPIView, generics.RetrieveAPIView):
    request_serializer = PollRequestSerializer
    response_serializer = PollResponseSerializer
    queryset = Poll.objects.select_related('vacancy').prefetch_related('questions').order_by('id')
    permission_classes = [PollViewPermission]

    def get_serializer_context(self):
        return {
            'mode': self.request.query_params.get('mode')
        }

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return self.response_serializer
        return self.request_serializer

    def perform_create(self, serializer):
        return serializer.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        poll = self.perform_create(serializer)
        serializer = self.response_serializer(poll)
        return Response(serializer.data, status=HTTP_201_CREATED)

    def get_object(self):
        vacancy_id = self.kwargs.get('id')
        poll = self.get_queryset().filter(vacancy_id=vacancy_id).last()
        return poll

    def get(self, request, *args, **kwargs):
        try:
            return self.retrieve(request, *args, **kwargs)
        except Poll.DoesNotExist:
            return NotFoundResponse


class PollTemplateView(generics.RetrieveAPIView):
    serializer_class = PollResponseSerializer
    queryset = PollTemplate.objects.prefetch_related('questions')
    permission_classes = [IsAdminUser | IsHR]

    def get_serializer_context(self):
        return {
            'mode': 'admin'
        }

    def get_object(self):
        poll_template_id = self.kwargs.get('id')
        poll_template = self.get_queryset().get(id=poll_template_id)
        return poll_template

    def get(self, request, *args, **kwargs):
        try:
            return self.retrieve(request, *args, **kwargs)
        except PollTemplate.DoesNotExist:
            return NotFoundResponse


class PollTemplateShortInfoView(generics.ListAPIView):
    serializer_class = PollTemplateShortInfoSerializer
    queryset = PollTemplate.objects.all()


class RoleVacanciesView(generics.ListAPIView):
    """Отдает список вакансий руководителя/рекрутера.

    query params:
    query - Поисковый запрос по названию или ФИО рекрутера вакансии
    status - Фильтр по статусу вакансии, при отсутствии - вернутся вакансии со всеми статусами
    """

    role: str = None
    serializer_class = MyVacancySerializer
    pagination_class = DataWrappingLimitOffsetPagination

    def get_queryset(self):
        user = self.request.user
        role = self.role

        query_params_serializer = VacancyQueryParamSerializer(data=self.request.query_params)
        query_params_serializer.is_valid(raise_exception=True)
        query_params = query_params_serializer.validated_data

        vacancy_role_to_q_map = {
            VacancyRoleChoices.MANAGER: Q(manager=user),
            VacancyRoleChoices.HR: ~Q(status=VacancyStatusChoices.MODERATION),
            VacancyRoleChoices.HEAD_HR: Q()
        }

        q = vacancy_role_to_q_map[role]

        full_name = Concat(
            F('recruiter__first_name'), Value(' '), F('recruiter__last_name'), output_field=CharField()
        )

        if query_params.get('status'):
            q &= Q(status=query_params.get('status'))
        if query_params.get('query'):
            title_q = Q(title__icontains=query_params.get('query'))
            recruiter_q = Q(full_name__icontains=query_params.get('query'))
            q &= (title_q | recruiter_q)
        if role == VacancyRoleChoices.HR:
            vacancy_owner_to_q_map = {
                VacancyOwnerChoices.ME: Q(recruiter=user),
                VacancyOwnerChoices.OTHER: ~Q(recruiter=user),
            }
            q &= vacancy_owner_to_q_map.get(query_params.get('owner'), Q())
        if query_params.get('recruiter'):
            q &= Q(recruiter=query_params.get('recruiter'))
        if role == VacancyRoleChoices.HEAD_HR:
            if query_params.get('status_exclude'):
                q &= ~Q(status__in=query_params.get('status_exclude'))
        if query_params.get('selection_type'):
            q &= Q(selection_type=query_params.get('selection_type'))
        is_viewed = VacancyViewed.objects.filter(vacancy=OuterRef('pk'), user=user)
        return Vacancy.objects.prefetch_related('replies').select_related('recruiter').annotate(
            full_name=full_name, is_new=~Exists(is_viewed)
        ).filter(q).order_by('-hot', '-id').distinct()


class RoleHeadHRVacanciesView(RoleVacanciesView):
    def patch(self, request, *args, **kwargs):
        serializer = VacancyPatchRecruiterSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return NoContentResponse


class VacancyFiltersView(generics.GenericAPIView):
    """Отдает value и label статусов вакансии."""

    class QueryParamsSerializer(serializers.Serializer):
        role = serializers.ChoiceField(choices=list(ROLE_TO_VACANCY_FILTERS.keys()))

    def get(self, request):
        query_serializer = self.QueryParamsSerializer(data=self.request.query_params)
        query_serializer.is_valid(raise_exception=True)
        role = query_serializer.validated_data.get('role')

        statuses = [VacancyStatusChoices(value).slug_name_dict for value in ROLE_TO_VACANCY_FILTERS[role]]
        return Response({'statuses': statuses})


class VacanciesReserveListView(generics.ListAPIView):
    """Отдает треки для кадрового резерва."""

    serializer_class = VacancyReserveSerializer
    queryset = VacancyReserve.objects.order_by('priority')
    pagination_class = DataWrappingLimitOffsetPagination


class VacancyTypesView(generics.ListAPIView):
    """Отдает список типов вакансий."""
    serializer_class = VacancyTypeSerializer
    queryset = VacancyType.objects.all()
    permission_classes = (IsHR | IsHeadHR | IsManager,)


class ReasonsView(generics.ListAPIView):
    """Отдает список причин открытия вакансий."""
    serializer_class = ReasonSerializer
    queryset = Reason.objects.all()
    permission_classes = (IsHR | IsHeadHR | IsManager,)


class WorkExperiencesView(generics.ListAPIView):
    """Отдает список опытов работы."""
    serializer_class = WorkExperienceSerializer
    queryset = WorkExperience.objects.all()
    permission_classes = (IsHR | IsHeadHR | IsManager,)


class WorkContractsView(generics.ListAPIView):
    """Отдает список типов контрактов."""
    serializer_class = WorkContractSerializer
    queryset = WorkContract.objects.all()
    permission_classes = (IsHR | IsHeadHR | IsManager,)


class RatesView(generics.ListAPIView):
    """Отдает список ставок."""
    serializer_class = RateSerializer
    queryset = Rate.objects.order_by('title')
    permission_classes = (IsHR | IsHeadHR | IsManager,)
