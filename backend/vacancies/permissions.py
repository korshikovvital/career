from rest_framework import permissions
from rest_framework.permissions import IsAdminUser

from core.permissions import ReadOnly
from users.permissions import IsHeadHR, IsHR, IsManager
from vacancies.enums import VacancyStatusChoices
from vacancies.serializers import VacancyDetailRecruiterUpdateSerializer


class PollViewPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        """
        Разрешает:
        Администраторам и сотрудникам HR - отправку опросов и получение опроса с правильными ответами на вопросы.
        Обычным сотрудникам и руководителям - только получение опроса без правильных ответов.
        """
        return (
            IsAdminUser().has_permission(request, view) or
            IsHR().has_permission(request, view) or (
                ReadOnly().has_permission(request, view) and
                request.query_params.get('mode') != 'admin'
            )
        )


class VacancyViewPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        """
        Разрешает:
        - HR и Head HR редактировать вакансию.
        - Head HR назначать рекрутера на вакансию.
        - Просматривать драфтовые вакансии HR и Админам.
        """
        if request.method == 'PATCH':
            return (
                IsHeadHR().has_permission(request, view) if view.serializer_class is VacancyDetailRecruiterUpdateSerializer
                else IsHR().has_permission(request, view) or IsHeadHR().has_permission(request, view)
            )
        elif request.method == 'GET':
            if obj.status == VacancyStatusChoices.MODERATION:
                return (
                    IsHR().has_permission(request, view) or IsAdminUser().has_permission(request, view)
                    or IsHeadHR().has_permission(request, view) or IsManager().has_permission(request, view)
                )
            return True
