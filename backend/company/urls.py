from django.urls import path

from company.views import (
    CompanyCitiesView,
    CompanyUnitsView,
    DepartmentsView,
    OfficesView,
    PositionsView
)

urlpatterns = [
    path('/cities', CompanyCitiesView.as_view()),
    path('/units', CompanyUnitsView.as_view()),
    path('/departments', DepartmentsView.as_view()),
    path('/positions', PositionsView.as_view()),
    path('/offices', OfficesView.as_view()),
]
