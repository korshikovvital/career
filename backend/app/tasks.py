import logging
from typing import List

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

from app.celery import celery

logger = logging.getLogger(__name__)


@celery.task
def send_templated_email(recipients: list, text_context: str, subject: str,
                         html_context: str = None, attachments: List[tuple] = None, _from: str = settings.EMAIL_SENDER):
    """
    Задача в Celery, для отправки email
    :param recipients: список email получателей
    :param text_context: текстовый шаблон
    :param html_context: html шаблон
    :param attachments: вложения к письму - список кортежей (filename, content)
    :param subject: заголовок письма
    :param _from: от кого письмо
    :return: None
    """
    if not settings.EMAIL_ENABLE:
        return

    msg = EmailMultiAlternatives(subject, text_context, _from, recipients)

    if html_context:
        msg.attach_alternative(html_context, 'text/html')

    if attachments:
        for attachment in attachments:
            msg.attach(*attachment)

    logger.info(f'Sending email to: {recipients}, subject: {subject}, from: {_from}')
    msg.send()
