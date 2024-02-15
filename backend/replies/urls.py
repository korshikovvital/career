from django.urls import path

from replies.views import (
    ReplyCreateView,
    ReplyFiltersView,
    ReplyInboxListView,
    ReplyInboxView,
    ReplyOutboxListView,
    ReplyOutboxView,
    TestDriveDatesView,
    TestDriveReplyView,
    VacancyReserveReplyView
)

urlpatterns = [
    path('', ReplyCreateView.as_view()),
    path('/outbox', ReplyOutboxListView.as_view()),
    path('/outbox/<int:id>', ReplyOutboxView.as_view()),
    path('/inbox', ReplyInboxListView.as_view()),
    path('/inbox/<int:id>', ReplyInboxView.as_view()),
    path('/filters', ReplyFiltersView.as_view()),
    path('/test_drive/dates', TestDriveDatesView.as_view()),
    path('/test_drive', TestDriveReplyView.as_view()),
    path('/reserve', VacancyReserveReplyView.as_view()),
]
