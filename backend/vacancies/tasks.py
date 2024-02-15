import logging

from django.conf import settings

from app.celery import celery
from app.utils import prepare_and_send_templated_email
from vacancies.enums import VacancyStatusChoices
from vacancies.models import Vacancy

logger = logging.getLogger(__name__)


@celery.task
def send_email_vacancy_without_test(vacancy_id: int):
    """
    Задача в Celery, для отправки email администраторам, если создана вакансия без теста
    :param vacancy_id: id вакансии по которой будет проверка
    :return: None
    """

    vacancy = Vacancy.objects.filter(pk=vacancy_id, status=VacancyStatusChoices.MODERATION).first()
    if vacancy:
        context = {
            'vacancy': vacancy,
            'hr_vacancies_link': settings.HR_VACANCIES_LINK
        }
        prepare_and_send_templated_email(
            [settings.EMAIL_ADMIN],
            'email/vacancies/vacancy_without_test',
            'Вакансия не опубликована',
            context
        )
        logger.info(f'Vacancy with id: {vacancy_id} without test. Status "{vacancy.status}". Sending email.')
    else:
        logger.info(
            f'Vacancy with id: {vacancy_id} not in status "{VacancyStatusChoices.MODERATION}". Email is not being sent.'
        )
