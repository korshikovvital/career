from django.urls import path

from core.views import InfoView

urlpatterns = [
    path('/info', InfoView.as_view()),
]
