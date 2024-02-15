from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django_prometheus.exports import ExportToDjangoView
from rest_framework import routers

from app.views import health_check_view

router = routers.DefaultRouter()

api_urls = [
    path('core', include('core.urls')),
    path('users', include('users.urls')),
    path('main', include('main.urls')),
    path('vacancies', include('vacancies.urls')),
    path('company', include('company.urls')),
    path('replies', include('replies.urls')),
    path('sap', include('sap.urls')),
]

urlpatterns = [
    path(f'{settings.API_PREFIX}/admin/', admin.site.urls),
    path('manage/health', health_check_view),
    path('manage/prometheus', ExportToDjangoView),
    path(f'{settings.API_PREFIX}/', include(api_urls)),
    path(f'{settings.API_PREFIX}/mdeditor/', include('mdeditor.urls')),
]

if settings.DEBUG_TOOLBAR_ENABLE:
    urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]

handler500 = 'app.handlers.handler500'
