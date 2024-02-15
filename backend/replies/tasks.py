from django.conf import settings

from app.celery import celery
from app.utils import prepare_and_send_templated_email
from replies.models import Step, TestDriveReply, VacancyReserveReply


@celery.task
def send_interview_notify():
    Step.objects.interview_notify_new_boss()


@celery.task
def send_emails_about_new_test_drive_reply(test_drive_reply_id: int) -> None:
    """
    Задача в Celery для отправки письма инициатору отклика на тест-драйв и исполнителю на техническую почту
    :param test_drive_reply_id: id заявки на тест-драйв
    :return: None
    """

    test_drive_reply = TestDriveReply.objects.get(id=test_drive_reply_id)
    user = test_drive_reply.user

    initiator_email = user.email
    executor_email = settings.EMAIL_TEST_DRIVE

    context = {
        'initiator': user,
        'test_drive_reply_date': test_drive_reply.date.strftime('%d.%m.%y')
    }

    # Отправляем письмо инициатору
    prepare_and_send_templated_email(
        recipients=[initiator_email],
        template='email/replies/new_test_drive_reply_for_initiator',
        subject='Тест-драйв в роли руководителя',
        context=context
    )

    # Отправляем письмо исполнителю
    prepare_and_send_templated_email(
        recipients=[executor_email],
        template='email/replies/new_test_drive_reply_for_executor',
        subject='Заявка на участие в тест-драйве',
        context=context
    )


@celery.task
def send_email_about_new_vacancy_reserve_reply(vacancy_reserve_reply_id: int) -> None:
    """Отправка письма о новой заявке на кадровый резерв."""

    vacancy_reserve_reply = VacancyReserveReply.objects.get(id=vacancy_reserve_reply_id)

    context = {
        'initiator': vacancy_reserve_reply.user,
        'vacancy_reserve_title': vacancy_reserve_reply.vacancy_reserve.title,
        'experience': vacancy_reserve_reply.get_experience_display(),
    }

    prepare_and_send_templated_email(
        [settings.EMAIL_VACANCY_RESERVE],
        template='email/replies/new_vacancy_reserve_reply',
        subject='Заявка на отбор в кадровый резерв',
        context=context,
    )
