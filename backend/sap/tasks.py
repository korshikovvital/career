import logging
from typing import List

from app import settings
from app.celery import celery
from app.utils import prepare_and_send_templated_email

from .clients import SAPHTTPClient
from .enum import SapMessageType, SapStatus
from .models import SapRequest
from .serializers import (
    ContestTypeSerializer,
    ReasonSerializer,
    SapCitySerializer,
    SapGradeSerializer,
    SapOfficeSerializer,
    VacancyTypeSerializer,
    WorkContractSerializer,
    WorkExperienceSerializer
)

logger = logging.getLogger(__name__)


@celery.task
def update_rates_from_sap():
    sap_client = SAPHTTPClient()
    sap_client.send_request("grade")


@celery.task
def update_cities_from_sap():
    sap_client = SAPHTTPClient()
    sap_client.send_request("city")


@celery.task
def update_addresses_from_sap():
    sap_client = SAPHTTPClient()
    sap_client.send_request("address")


@celery.task
def update_vacancies_types_from_sap():
    sap_client = SAPHTTPClient()
    sap_client.send_request("vacancy_type")


@celery.task
def update_contests_types_from_sap():
    sap_client = SAPHTTPClient()
    sap_client.send_request("contest_type")


@celery.task
def update_reasons_from_sap():
    sap_client = SAPHTTPClient()
    sap_client.send_request("reason")


@celery.task
def update_work_contracts_from_sap():
    sap_client = SAPHTTPClient()
    sap_client.send_request("work_contract")


@celery.task
def update_work_experiences_from_sap():
    sap_client = SAPHTTPClient()
    sap_client.send_request("work_experience")


@celery.task
def create_instances(
        object_type: str,
        data: List[dict]
) -> None:
    serializer_map = {
        'grade': SapGradeSerializer,
        'city': SapCitySerializer,
        'address': SapOfficeSerializer,
        'vacancy_type': VacancyTypeSerializer,
        'contest_type': ContestTypeSerializer,
        'reason': ReasonSerializer,
        'work_contract': WorkContractSerializer,
        'work_experience': WorkExperienceSerializer

    }

    serializer = serializer_map.get(object_type)(data=data, many=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()


@celery.task
def delete_successful_saprequests():
    SapRequest.objects.filter(status=SapStatus.SUCCESS).delete()


@celery.task
def send_candidate_to_sap(reply_id: int):
    sap_client = SAPHTTPClient()
    sap_client.update_reply_in_sap(reply_id, SapMessageType.FEEDBACK.value)


@celery.task
def update_reply_resume_status_in_sap(reply_id: int):
    sap_client = SAPHTTPClient()
    sap_client.update_reply_in_sap(reply_id, SapMessageType.RESUME_STATUS.value)


@celery.task
def update_reply_interview_status_in_sap(reply_id: int):
    sap_client = SAPHTTPClient()
    sap_client.update_reply_in_sap(reply_id, SapMessageType.INTERVIEW_STATUS.value)


@celery.task
def send_vacancy_to_sap(vacancy_id: int):
    sap_client = SAPHTTPClient()
    sap_client.send_vacancy(vacancy_id)


@celery.task
def send_extension_vacancy_publication(vacancy_id: int):
    sap_client = SAPHTTPClient()
    sap_client.send_extension_vacancy_publication(vacancy_id)


@celery.task
def check_sap_requests_status():
    error_sent_requests = SapRequest.objects.filter(status__in=[SapStatus.ERROR, SapStatus.SENT])
    if error_sent_requests:
        context = {
            'error_sent_requests': error_sent_requests,
        }
        prepare_and_send_templated_email(
            [settings.EMAIL_ADMIN],
            'email/sap/sap_requests_status',
            'SapRequest status ERROR or SENT',
            context
        )
        logger.info('SapRequest status ERROR or SENT". Sending email.')
    else:
        logger.info(
            'SapRequest status ERROR or SENT". Email is not being sent.'
        )
