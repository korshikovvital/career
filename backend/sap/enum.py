from django.db import models


class SapStatus(models.TextChoices):
    ERROR = 'Ошибка'
    SUCCESS = 'Успешно'
    SENT = 'Отправлен'


class SapMessageType(models.TextChoices):
    FEEDBACK = 'feedback', 'Отклик'
    RESUME_STATUS = 'resume_status', 'Статус резюме'
    INTERVIEW_STATUS = 'interview_status', 'Статус интервью с руководителем'
