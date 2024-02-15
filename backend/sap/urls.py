from django.urls import path

from .views import (
    SapCallbackView,
    SapCloseVacancyView,
    SapRecruiterView,
    SapRejectReplyView
)

urlpatterns = [
    path('/callback', SapCallbackView.as_view()),
    path('/recruiter', SapRecruiterView.as_view()),
    path('/vacancy/close', SapCloseVacancyView.as_view()),
    path('/candidate/reject', SapRejectReplyView.as_view())
]
