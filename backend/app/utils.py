import logging
from typing import List

from django.conf import settings
from django.template.exceptions import TemplateDoesNotExist, TemplateSyntaxError
from django.template.loader import get_template

from app.tasks import send_templated_email

logger = logging.getLogger(__name__)


def prepare_and_send_templated_email(recipients: list, template: str, subject: str, context: dict,
                                     attachments: List[tuple] = None, _from: str = settings.EMAIL_SENDER):
    """
    Производит рендеринг шаблона письма и запускает задачу в Celery, для отправки email
    :param recipients: список email получателей
    :param context: словарь данных для рендеринга шаблона
    :param template: путь к шаблону без расширения (модуль сам подставит расширения txt, html и попытается найти шаблон)
    :param attachments: вложения к письму - список кортежей (filename, content)
    :param subject: заголовок письма
    :param _from: от кого письмо
    :return: None
    """
    if not settings.EMAIL_ENABLE:
        return

    html_context = None

    try:
        text_context = get_template(f'{template}.txt').render(context)
    except TemplateDoesNotExist:
        logger.error(f'Шаблон {template}.txt не найден')
        return
    except TemplateSyntaxError as error:
        logger.error(f'Шаблон {template}.txt имеет синтаксические ошибки. {error}')
        return

    try:
        html_context = get_template(f'{template}.html').render(context)
    except (TemplateDoesNotExist, TemplateSyntaxError) as error:
        logger.info(f'Шаблон {template}.html не найден или имеет синтаксические ошибки. Сообщение ошибки: {error}')

    if settings.EMAIL_SUBJECT_PREFIX:
        if subject:
            subject = f'{settings.EMAIL_SUBJECT_PREFIX} - {subject}'

    send_templated_email.delay(recipients, text_context, subject, html_context, attachments, _from)
