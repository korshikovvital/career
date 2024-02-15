import logging

from django.conf import settings
from django.db import models
from django.utils import timezone

from app.models import TimestampedModel
from app.utils import prepare_and_send_templated_email
from core.utils import file_path
from replies.enums import (
    ExperienceChoices,
    ReplyStatusChoices,
    StepResolutionChoices,
    StepRoleChoices,
    StepStateChoices,
    TitleStateChoices
)

logger = logging.getLogger(__name__)


class Reply(TimestampedModel):
    user = models.ForeignKey('users.User', on_delete=models.PROTECT, verbose_name='Соискатель', related_name='replies')
    vacancy = models.ForeignKey(
        'vacancies.Vacancy',
        on_delete=models.PROTECT,
        verbose_name='Вакансия',
        related_name='replies'
    )
    poll = models.ForeignKey(
        'vacancies.Poll',
        on_delete=models.PROTECT,
        verbose_name='Опросник',
        related_name='replies',
        blank=True,
        null=True
    )
    resume = models.FileField('Резюме', upload_to=file_path, blank=True, null=True)
    comment = models.TextField('Комментарий', blank=True, null=True)
    status = models.CharField('Статус', max_length=100, choices=ReplyStatusChoices.choices)
    experience = models.CharField(
        'Стаж работы сотрудника в текущей должности',
        max_length=50,
        choices=ExperienceChoices.choices
    )

    class Meta:
        verbose_name = 'Отклик на вакансию'
        verbose_name_plural = 'Отклики на вакансию'
        constraints = [
            models.UniqueConstraint(fields=['user', 'vacancy'],
                                    name='%(app_label)s_%(class)s_is_one_user_reply_to_vacancy')
        ]

    def create_steps(self):
        if self.steps.all():
            return False, 'Маршрут уже создан для данного отклика'
        for key, value in self.route.items():
            step = Step.objects.create(
                reply=self,
                index=key,
                title=value.get('title'),
                role=value.get('role'),
                user=value.get('user'),
                state=StepStateChoices.EXPECTED
            )
            if key == 1:
                step.activate()
        return True, 'Маршрут создан'

    @property
    def route(self):  # на основе этого буду генерировать маршрут для заявки, и выполнять действия при переходе
        return {
            1: {
                'user': self.vacancy.manager,
                'title': TitleStateChoices.AGREEMENT,  # Наименование шага
                'role': StepRoleChoices.NEW_BOSS,  # Роль участника шага
                'resolutions': [StepResolutionChoices.APPROVED,
                                StepResolutionChoices.REJECTED,
                                StepResolutionChoices.INTERVIEW],
                'activate_state': StepStateChoices.ACTIVE,
                'next': {
                    StepResolutionChoices.APPROVED: {
                        'step': 'next_2',  # Переход через шаг (на 2 шага вперед)
                        'reply_status': ReplyStatusChoices.HIRED,
                        'step_status': ReplyStatusChoices.HIRED,
                        'state': StepStateChoices.END

                    },
                    StepResolutionChoices.REJECTED: {
                        'step': 'stop',  # Остановка процесса
                        'reply_status': ReplyStatusChoices.REJECTED,
                        'step_status': ReplyStatusChoices.REJECTED,
                        'state': StepStateChoices.END
                    },
                    StepResolutionChoices.INTERVIEW: {
                        'step': 'next_1',
                        'reply_status': ReplyStatusChoices.INTERVIEW,
                        'step_status': ReplyStatusChoices.APPROVED,
                        'state': StepStateChoices.HIDDEN
                    }
                }
            },
            2: {
                'user': self.vacancy.manager,
                'title': TitleStateChoices.INTERVIEW,  # Наименование шага
                'role': StepRoleChoices.NEW_BOSS,  # Роль участника шага
                'resolutions': [StepResolutionChoices.APPROVED, StepResolutionChoices.REJECTED],
                'activate_state': StepStateChoices.ACTIVE,
                'next': {
                    StepResolutionChoices.APPROVED: {
                        'step': 'next_1',
                        'reply_status': ReplyStatusChoices.HIRED,
                        'step_status': ReplyStatusChoices.APPROVED,
                        'state': StepStateChoices.HIDDEN
                    },
                    StepResolutionChoices.REJECTED: {
                        'step': 'stop',  # Остановка процесса
                        'reply_status': ReplyStatusChoices.REJECTED,
                        'step_status': ReplyStatusChoices.REJECTED,
                        'state': StepStateChoices.END
                    },
                }
            },
            3: {
                'user': self.vacancy.manager,
                'title': TitleStateChoices.HIRED,  # Наименование шага
                'role': StepRoleChoices.NEW_BOSS,  # Роль участника шага
                'resolutions': [StepResolutionChoices.REJECTED],
                'activate_state': StepStateChoices.ACTIVE,
                'next': {
                    StepResolutionChoices.REJECTED: {
                        'step': 'stop',  # Остановка процесса
                        'reply_status': ReplyStatusChoices.REJECTED,
                        'step_status': ReplyStatusChoices.REJECTED,
                        'state': StepStateChoices.END
                    },
                }
            }
        }


class StepManager(models.Manager):

    def interview_notify_new_boss(self):
        steps_need_notify = Step.objects.select_related(
            'reply', 'user'
        ).filter(
            state=StepStateChoices.ACTIVE,
            role=StepRoleChoices.NEW_BOSS,
            title=TitleStateChoices.INTERVIEW
        )
        for step in steps_need_notify:
            if (timezone.now().date() - step.activation_date.date()).days % settings.REMINDER_INTERVAL == 0:
                step.email_interview_for_manager(first=False)


class Step(models.Model):
    reply = models.ForeignKey(
        'replies.Reply',
        related_name='steps',
        verbose_name='Отклик на вакансию',
        on_delete=models.CASCADE)
    index = models.PositiveIntegerField('Номер текущего шага', default=1)
    title = models.CharField('Наименование шага', max_length=250, choices=TitleStateChoices.choices)
    role = models.CharField('Роль', max_length=100, choices=StepRoleChoices.choices)
    user = models.ForeignKey('users.User', on_delete=models.PROTECT, verbose_name='Участник шага')
    resolution = models.CharField(
        'Решение',
        max_length=100,
        null=True,
        blank=True,
        choices=StepResolutionChoices.choices
    )
    comment = models.TextField('Комментарий к решению', null=True, blank=True)
    state = models.CharField('Состояние', max_length=100, choices=StepStateChoices.choices)
    status = models.CharField('Статус', max_length=100, choices=ReplyStatusChoices.choices, null=True, blank=True)
    is_viewed = models.BooleanField('Прочитано', default=False)
    activation_date = models.DateTimeField('Дата активации шага', null=True, blank=True)

    objects = StepManager()

    class Meta:
        verbose_name = 'Шаг маршрута'
        verbose_name_plural = 'Маршруты заявок'
        constraints = [
            models.UniqueConstraint(fields=['reply', 'index'],
                                    name='%(app_label)s_%(class)s_is_unique_step_number_for_reply')
        ]

    @property
    def context(self):
        return {
            'user': self.reply.user,
            'vacancy': self.reply.vacancy,
            'step_user': self.user,
            'manager': self.reply.vacancy.manager,
            'request_link': f'{settings.INBOX_LINK}/{self.id}',
            'inbox_link': settings.INBOX_LINK,
            'outbox_link': settings.OUTBOX_LINK,
            'hr_vacancies_link': settings.HR_VACANCIES_LINK,
        }

    def activate(self):
        self.state = self.reply.route[self.index]['activate_state']
        self.status = self.reply.status
        self.activation_date = timezone.now()
        self.save()
        if self.title == TitleStateChoices.AGREEMENT:
            template_for_current_boss = 'email/replies/new_reply_for_current_boss'
            subject_for_current_boss = 'Ваш сотрудник откликнулся на вакансию'
            template_for_new_boss = 'email/replies/new_reply_for_new_boss'
            subject_for_recruiter = subject_for_new_boss = 'Отклик на вакансию'
            template_for_recruiter = 'email/replies/new_reply_for_recruiter'

            # Отправляем письмо текущему руководителю
            if self.reply.user.manager:
                prepare_and_send_templated_email(
                    recipients=[self.reply.user.manager.email],
                    template=template_for_current_boss,
                    subject=subject_for_current_boss,
                    context=self.context
                )

            vacancy_manager = self.reply.vacancy.manager
            vacancy_manager_email = vacancy_manager.email if vacancy_manager else None
            if vacancy_manager_email:
                # Отправляем письмо будущему руководителю
                prepare_and_send_templated_email(
                    recipients=[vacancy_manager_email],
                    template=template_for_new_boss,
                    subject=subject_for_new_boss,
                    context=self.context
                )

            vacancy_recruiter = self.reply.vacancy.recruiter
            vacancy_recruiter_email = vacancy_recruiter.email if vacancy_recruiter else None
            if vacancy_recruiter_email:
                # Отправляем письмо рекрутеру
                prepare_and_send_templated_email(
                    recipients=[vacancy_recruiter_email],
                    template=template_for_recruiter,
                    subject=subject_for_recruiter,
                    context=self.context
                )

        if self.title == TitleStateChoices.INTERVIEW:
            self.email_interview_for_manager()  # Напоминание менеджеру и рекрутеру запланировать собеседование
            # Сообщение сотруднику, что его позвали на собеседование.
            prepare_and_send_templated_email(
                [self.reply.user.email],
                'email/replies/invite_interview',
                'Приглашение на собеседование',
                self.context
            )
        if self.title == TitleStateChoices.HIRED:
            prepare_and_send_templated_email(  # Уведомление сотруднику
                [self.reply.user.email],
                'email/replies/hired_user',
                'Твоя заявка согласована',
                self.context
            )
            if self.reply.vacancy.manager:
                prepare_and_send_templated_email(  # Уведомление будущему руководителю
                    [self.reply.vacancy.manager.email],
                    'email/replies/hired_for_new_boss',
                    'Запусти процесс перевода сотрудника',
                    self.context
                )
            # Уведомление рекрутеру и администраторам
            prepare_and_send_templated_email(  # Уведомление рекрутеру и администраторам
                [self.reply.vacancy.recruiter.email if self.reply.vacancy.recruiter else None, settings.EMAIL_ADMIN],
                'email/replies/hired_for_recruiter_and_admins',
                'Кандидат на вакансию согласован',
                self.context
            )

    def end_activity(self, resolution=None, comment=None, step=None, reply_status=None, step_status=None, state=None):
        if resolution:
            self.resolution = resolution
        if comment:
            self.comment = comment
        if reply_status:

            self.reply.status = reply_status
            self.reply.save()

            from sap.tasks import (
                update_reply_interview_status_in_sap,
                update_reply_resume_status_in_sap,
            )

            if self.index == 1:
                update_reply_resume_status_in_sap.delay(self.reply_id)

                if reply_status == ReplyStatusChoices.HIRED:
                    update_reply_interview_status_in_sap.delay(self.reply_id)

            elif self.index == 2:
                update_reply_interview_status_in_sap.delay(self.reply_id)

        if step_status:
            self.status = step_status
        if state:
            self.state = state
        step_function, _, atr = step.partition('_')
        if step_function == 'next':
            self.next(int(atr))
        elif step_function == 'stop':
            self.stop()
        self.save()

    def next(self, steps_number):
        next_step = Step.objects.filter(reply=self.reply, index=(self.index + steps_number)).first()
        if next_step:
            next_step.activate()
        missed_steps = Step.objects.filter(
            reply=self.reply,
            index__lt=(self.index + steps_number),
            index__gt=self.index
        ).update(
            state=StepStateChoices.HIDDEN,
            status=ReplyStatusChoices.APPROVED
        )
        if missed_steps > 0:
            logger.info(f'В согласовании заявки {self.reply.id} было пропущено {missed_steps} шагов.')

    def stop(self):
        Step.objects.filter(
            reply=self.reply,
            index__gt=self.index
        ).update(
            state=StepStateChoices.STOP
        )
        prepare_and_send_templated_email(
            [self.reply.user.email],
            'email/replies/reject_user',
            'Заявка отклонена',
            self.context
        )

    def email_interview_for_manager(self, first=True):
        if first:
            template = 'email/replies/interview_for_manager_first'
        else:
            template = 'email/replies/interview_for_manager'
        recipients = []
        if self.reply.vacancy.manager:
            recipients.append(self.reply.vacancy.manager.email)
        if self.reply.vacancy.recruiter:
            recipients.append(self.reply.vacancy.recruiter.email)
        prepare_and_send_templated_email(
            recipients,
            template,
            'Запланируй собеседование',
            self.context
        )


class TestDriveDate(models.Model):
    date = models.DateField(
        verbose_name='Дата тест-драйва'
    )
    is_active = models.BooleanField(
        verbose_name='Активна',
        default=True,
    )

    def __str__(self):
        return f'Дата тест-драйва: {self.date}'

    class Meta:
        verbose_name = 'Тест-драйв: дата'
        verbose_name_plural = 'Тест-драйв: даты'


class TestDriveReply(TimestampedModel):
    user = models.ForeignKey(
        to='users.User',
        verbose_name='Соискатель',
        on_delete=models.PROTECT,
        related_name='test_drive_replies'
    )
    date = models.DateField(
        verbose_name='Дата тест-драйва'
    )

    def __str__(self):
        return f'Заявка на тест-драйв от {self.user}'

    class Meta:
        verbose_name = 'Тест-драйв: заявка'
        verbose_name_plural = 'Тест-драйв: заявки'


class VacancyReserveReply(TimestampedModel):
    user = models.ForeignKey(
        'users.User',
        verbose_name='Соискатель',
        on_delete=models.PROTECT,
        related_name='vacancy_reserve_replies'
    )
    vacancy_reserve = models.ForeignKey(
        'vacancies.VacancyReserve',
        verbose_name='Кадровый резерв',
        on_delete=models.PROTECT,
        related_name='vacancy_reserve_replies'
    )
    experience = models.CharField(
        'Стаж работы сотрудника в текущей должности',
        max_length=50,
        choices=ExperienceChoices.choices
    )

    def __str__(self):
        return f'Отклик от {self.user.full_name} на кадровый резерв {self.vacancy_reserve.title}'

    class Meta:
        verbose_name = 'Отклик на кадровый резерв'
        verbose_name_plural = 'Отклики на кадровый резерв'
