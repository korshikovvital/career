from django.db.models import CharField, F, Q, Value
from django.db.models.functions import Concat
from rest_framework import generics
from rest_framework.response import Response

from app.pagination import DataWrappingLimitOffsetPagination
from app.responses import NoContentResponse
from core.permissions import ObjectOwnerOrAdminUser
from replies.enums import ReplyStatusChoices, StepStateChoices
from replies.models import Reply, Step, TestDriveDate
from replies.serializers import (
    ReplyInboxListSerializer,
    ReplyInboxSerializer,
    ReplyInboxUpdateSerializer,
    ReplyOutboxSerializer,
    ReplyOutboxUpdateSerializer,
    TestDriveDateSerializer,
    TestDriveReplySerializer,
    VacancyReplyCreateSerializer,
    VacancyReserveReplySerializer
)
from users.permissions import IsHeadHR, IsHR, IsManager


class ReplyOutboxListView(generics.ListAPIView):
    serializer_class = ReplyOutboxSerializer
    pagination_class = DataWrappingLimitOffsetPagination

    def get_queryset(self):
        q = Q(user=self.request.user)

        status = self.request.query_params.get('status')
        if status:
            q &= Q(status=status)

        return Reply.objects.prefetch_related('steps', 'steps__user').filter(q).order_by("-id")


class ReplyInboxListView(generics.ListAPIView):
    # По логике на самом деле во входящих пользователям доступны шаги по заявкам, а не сами заявки
    serializer_class = ReplyInboxListSerializer
    pagination_class = DataWrappingLimitOffsetPagination
    permission_classes = (IsHR | IsManager | IsHeadHR,)

    def get_queryset(self):
        # Только активные или завершенные шаги
        q = Q(state__in=(StepStateChoices.ACTIVE, StepStateChoices.END))

        if not (self.request.user.has_perm('users.is_hr') or self.request.user.has_perm('users.is_head_hr')):
            q &= Q(user=self.request.user)

        status = self.request.query_params.get('status')
        vacancy_id = self.request.query_params.get('vacancy_id')
        query = self.request.query_params.get('query')

        candidate_full_name = Concat(
            F('reply__user__first_name'), Value(' '), F('reply__user__last_name'), output_field=CharField()
        )

        if status:
            q &= Q(status=status)
        if vacancy_id:
            q &= Q(reply__vacancy__id=vacancy_id)
        if query:
            vacancy_title_q = Q(reply__vacancy__title__icontains=query)
            candidate_q = Q(candidate_full_name__icontains=query)
            q &= vacancy_title_q | candidate_q

        return Step.objects.select_related(
            'reply', 'reply__user'
        ).annotate(
            candidate_full_name=candidate_full_name
        ).filter(q).order_by('is_viewed', '-reply__modified', '-reply__id', '-activation_date')


class ReplyInboxView(generics.RetrieveUpdateAPIView):
    serializer_class = ReplyInboxSerializer
    lookup_field = 'id'
    queryset = Step.objects.select_related(
        'reply', 'reply__user', 'reply__vacancy', 'reply__vacancy__unit'
    )
    serializer_update_class = ReplyInboxUpdateSerializer
    permission_classes = (ObjectOwnerOrAdminUser | IsHR | IsHeadHR,)

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return self.serializer_update_class
        return super().get_serializer_class()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.is_viewed:
            instance.is_viewed = True
            instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class ReplyOutboxView(generics.UpdateAPIView):
    lookup_field = 'id'
    serializer_response_class = ReplyOutboxSerializer
    serializer_class = ReplyOutboxUpdateSerializer
    permission_classes = [ObjectOwnerOrAdminUser]
    queryset = Reply.objects.select_related('vacancy').prefetch_related('steps')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        response_serializer = self.serializer_response_class(serializer.instance)
        return Response(response_serializer.data)


class ReplyCreateView(generics.CreateAPIView):
    serializer_class = VacancyReplyCreateSerializer

    def post(self, request, *args, **kwargs):
        try:
            response = self.create(request, *args, **kwargs)
        except ValueError as error:
            return Response(
                data={'text': str(error)},
                status=200
            )
        else:
            return response


class ReplyFiltersView(generics.GenericAPIView):
    """Отдает label и value статусов откликов на вакансии."""

    def get(self, request):
        statuses = [
            ReplyStatusChoices(value).slug_name_dict for value in ReplyStatusChoices.values
            if value != ReplyStatusChoices.APPROVED.value
        ]
        return Response({'statuses': statuses})


class TestDriveDatesView(generics.ListAPIView):
    queryset = TestDriveDate.objects.filter(is_active=True).order_by('date')
    serializer_class = TestDriveDateSerializer


class TestDriveReplyView(generics.CreateAPIView):
    serializer_class = TestDriveReplySerializer

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)
        return NoContentResponse


class VacancyReserveReplyView(generics.CreateAPIView):
    serializer_class = VacancyReserveReplySerializer

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)
        return NoContentResponse
