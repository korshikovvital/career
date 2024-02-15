from django.urls import path
from rest_framework.permissions import IsAdminUser

from users.permissions import IsHeadHR, IsHR, IsManager
from vacancies.enums import VacancyRoleChoices
from vacancies.views import (
    FactoidView,
    PollTemplateShortInfoView,
    PollTemplateView,
    PollView,
    RatesView,
    ReasonsView,
    RoleHeadHRVacanciesView,
    RoleVacanciesView,
    VacanciesListCreateView,
    VacanciesReserveListView,
    VacancyFiltersView,
    VacancyTypesView,
    VacancyView,
    WorkContractsView,
    WorkExperiencesView
)

urlpatterns = [
    path('', VacanciesListCreateView.as_view()),
    path('/<int:id>', VacancyView.as_view()),
    path('/factoids', FactoidView.as_view()),
    path('/<int:id>/poll', PollView.as_view()),
    path('/poll_templates/<int:id>', PollTemplateView.as_view()),
    path('/poll_templates', PollTemplateShortInfoView.as_view()),
    path('/filters', VacancyFiltersView.as_view()),
    path('/hr', RoleVacanciesView.as_view(role=VacancyRoleChoices.HR, permission_classes=[IsAdminUser | IsHR | IsHeadHR])),
    path('/manager', RoleVacanciesView.as_view(role=VacancyRoleChoices.MANAGER, permission_classes=[IsAdminUser | IsManager])),
    path('/head_hr', RoleHeadHRVacanciesView.as_view(role=VacancyRoleChoices.HEAD_HR, permission_classes=[IsAdminUser | IsHeadHR])),
    path('/reserve', VacanciesReserveListView.as_view()),
    path('/types', VacancyTypesView.as_view()),
    path('/reasons', ReasonsView.as_view()),
    path('/contracts', WorkContractsView.as_view()),
    path('/experiences', WorkExperiencesView.as_view()),
    path('/rates', RatesView.as_view()),
]
