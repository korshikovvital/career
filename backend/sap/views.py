import logging

from django.conf import settings
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from app import errors
from vacancies.models import Vacancy

from .enum import SapStatus
from .models import SapRequest
from .serializers import (
    SapCloseVacancySerializer,
    SapRecruiterSerializer,
    SapRejectReplySerializer
)
from .tasks import create_instances
from .utils import chunks

logger = logging.getLogger(__name__)


class SapCallbackView(APIView):
    def post(self, request):
        saprequest = SapRequest.objects.filter(guid=request.data.get('guid', '')).first()
        status = request.data.get('status', 'S')

        if status == 'S':
            if not saprequest:
                return Response(data=errors.SAP_GUID_NOT_FOUND, status=404)

            saprequest.status = SapStatus.SUCCESS
            saprequest.response_sap = request.data
            saprequest.save()

            if saprequest.endpoint == settings.SAP_HR_REQUEST_ENDPOINT:

                object_type = request.data.get('objectType')
                data = request.data.get(object_type, [])

                for batch in chunks(data, settings.SAP_DATA_BATCH_SIZE):
                    create_instances.delay(object_type=object_type, data=batch)

                return Response(status=201)

            elif saprequest.endpoint == settings.SAP_HR_VACANCY_ENDPOINT:
                Vacancy.objects.filter(
                    pk=int(request.data['id_career_routes'])
                ).update(
                    sap_id=request.data['nb']
                )
                return Response(status=200)

            elif saprequest.endpoint == settings.SAP_HR_VACANCY_EXTEND_ENDPOINT:
                return Response(status=200)

            elif saprequest.endpoint == settings.SAP_HR_CANDIDATE_ENDPOINT:
                return Response(status=200)

        if status == 'E':
            saprequest.status = SapStatus.ERROR
            saprequest.response_sap = request.data
            saprequest.save()
            logger.error(f'Error getting request from SAP, data: {request.data}')
            return Response(status=400)


class SapRecruiterView(generics.CreateAPIView):
    serializer_class = SapRecruiterSerializer


class SapCloseVacancyView(generics.CreateAPIView):
    serializer_class = SapCloseVacancySerializer


class SapRejectReplyView(generics.CreateAPIView):
    serializer_class = SapRejectReplySerializer
