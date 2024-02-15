from django.urls import path

from main.views import InvitationView, MainView, PollView

urlpatterns = [
    path('', MainView.as_view()),
    path('/poll', PollView.as_view()),
    path('/invite', InvitationView.as_view())
]
