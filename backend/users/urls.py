from django.urls import path

from users.views import UserShortInfoView, UsersListView

urlpatterns = [
    path('', UsersListView.as_view()),
    path('/short-info', UserShortInfoView.as_view()),
]
