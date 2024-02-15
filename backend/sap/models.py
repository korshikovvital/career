import logging

from django.db import models

from app.models import TimestampedModel

from .enum import SapStatus

logger = logging.getLogger(__name__)


class SapRequest(TimestampedModel):
    guid = models.CharField(primary_key=True, max_length=120)
    status = models.CharField(max_length=120, choices=SapStatus.choices)
    request_body = models.JSONField(null=True, blank=True, default=dict)
    response_sap = models.JSONField(null=True, blank=True, default=dict)
    endpoint = models.CharField(max_length=240, blank=True, null=True)
    task = models.CharField(
        max_length=240,
        blank=True,
        null=True,
        help_text='Название celery task, которым был текущий sap request создан'
    )

    class Meta:
        verbose_name = 'Запрос в Sap'
        verbose_name_plural = 'Запросы в Sap'

    def send(self):
        from .clients import SAPHTTPClient
        client = SAPHTTPClient()
        resp = client.http_client.post(
            url=f'{client.base_url}/{self.endpoint}',
            json=self.request_body,
            headers=client.headers
        )
        if resp.status_code == 202:
            logger.info(f"Received response for information with number {self.guid}")
            self.status = SapStatus.SENT
            self.save()
        else:
            logger.error(f"Error with sending request to SAP. Received response status - {resp.status_code}")
