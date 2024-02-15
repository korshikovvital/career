import base64
import logging
import uuid
from typing import Union

import httpx
from django.conf import settings

from replies.models import Reply
from vacancies.models import Vacancy

from .enum import SapMessageType, SapStatus
from .models import SapRequest
from .serializers import SapExtensionPublication, SapReplySerializer, SapVacancySerializer

logger = logging.getLogger(__name__)


class SAPHTTPClient:
    def __init__(self):
        self.authentication_str = f"{settings.SAP_HR_TECH_USERNAME}:{settings.SAP_HR_TECH_PASSWORD}".encode('ascii')
        self.http_client = httpx.Client(verify=False)
        self.base_url = settings.SAP_HR_BASE_URL
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Basic {base64.b64encode(self.authentication_str).decode()}'
        }

    def send_request(self, object_type):
        guid = uuid.uuid4()
        url = f'{self.base_url}/{settings.SAP_HR_REQUEST_ENDPOINT}'
        data = {
            "guid": str(guid),
            "objectType": object_type
        }
        resp = self.http_client.post(
            url=url, json=data, headers=self.headers
        )
        if resp.status_code == 202:
            logger.info(f"Received response for information with number {guid}")
            SapRequest.objects.create(guid=guid, endpoint=settings.SAP_HR_REQUEST_ENDPOINT, status=SapStatus.SENT,
                                      request_body=data)
        else:
            logger.error(f"Error with sending request to SAP. Received response status - {resp.status_code}")

    def send_vacancy(self, vacancy_id):
        guid = uuid.uuid4()
        vacancy = Vacancy.objects.get(id=vacancy_id)
        url = f'{self.base_url}/{settings.SAP_HR_VACANCY_ENDPOINT}'
        serializer = SapVacancySerializer(vacancy)
        data = {
            "guid": str(guid),
        }
        data.update(serializer.data)
        resp = self.http_client.post(
            url=url, json=data, headers=self.headers
        )
        if resp.status_code == 202:
            logger.info(f"Received response for information with number {guid}")
            SapRequest.objects.create(guid=guid,
                                      endpoint=settings.SAP_HR_VACANCY_ENDPOINT,
                                      task=f'send_vacancy({vacancy_id})',
                                      status=SapStatus.SENT,
                                      request_body=data)
        else:
            logger.error(f"Error with sending request to SAP. Received response status - {resp.status_code}")

    def send_extension_vacancy_publication(self, vacancy_id):
        guid = uuid.uuid4()
        vacancy = Vacancy.objects.get(id=vacancy_id)
        url = f'{self.base_url}/{settings.SAP_HR_VACANCY_EXTEND_ENDPOINT}'
        serializer = SapExtensionPublication(vacancy)
        data = {
            "guid": str(guid),
        }
        data.update(serializer.data)
        resp = self.http_client.post(
            url=url, json=data, headers=self.headers
        )
        if resp.status_code == 202:
            logger.info(f"Received response for information with number {guid}")
            SapRequest.objects.create(guid=guid,
                                      endpoint=settings.SAP_HR_VACANCY_EXTEND_ENDPOINT,
                                      task=f'send_extension_vacancy_publication({vacancy_id})',
                                      status=SapStatus.SENT,
                                      request_body=data)
        else:
            logger.error(f"Error with sending request to SAP. Received response status - {resp.status_code}")

    def update_reply_in_sap(
            self,
            reply_id: int,
            message_type: Union[
                SapMessageType.FEEDBACK.value,
                SapMessageType.RESUME_STATUS.value,
                SapMessageType.INTERVIEW_STATUS.value
            ]
    ):
        guid = uuid.uuid4()
        reply = Reply.objects.get(id=reply_id)
        url = f'{self.base_url}/{settings.SAP_HR_CANDIDATE_ENDPOINT}'

        if message_type in SapMessageType:

            serializer = SapReplySerializer(
                reply,
                context={'message_type': message_type}
            )
            data = {
                "guid": str(guid),
            }
            data.update(serializer.data)
            resp = self.http_client.post(
                url=url, json=data, headers=self.headers
            )
            if resp.status_code == 202:
                logger.info(f"Received response for information with number {guid}")
                SapRequest.objects.create(guid=guid,
                                          endpoint=settings.SAP_HR_CANDIDATE_ENDPOINT,
                                          status=SapStatus.SENT,
                                          task=f'update_reply_in_sap({reply_id}, "{message_type}")',
                                          request_body=data)
            else:
                logger.error(f"Error with sending request to SAP. Received response status - {resp.status_code}")
        else:
            logger.error("Message type is wrong! Check SapMessageType. Skip sending status to sap.")
