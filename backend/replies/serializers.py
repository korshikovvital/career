import logging

from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

import app.errors as errors
from app.utils import prepare_and_send_templated_email
from company.enums import SelectionTypeChoices
from replies.enums import (
    ExperienceChoices,
    ReplyStatusChoices,
    StepResolutionChoices,
    StepRoleChoices,
    StepStateChoices,
    TitleStateChoices
)
from replies.models import Reply, Step, TestDriveDate, TestDriveReply, VacancyReserveReply
from replies.tasks import (
    send_email_about_new_vacancy_reserve_reply,
    send_emails_about_new_test_drive_reply
)
from sap.tasks import (
    send_candidate_to_sap,
    update_reply_interview_status_in_sap,
    update_reply_resume_status_in_sap
)
from users.serializers import UserReplyAvatarSerializer
from vacancies.enums import QuestionType, VacancyStatusChoices
from vacancies.models import Question, Restrict, UserAnswer, Vacancy, VacancyReserve
from vacancies.serializers import UserTestAnswerSerializer, VacancyShortReplySerializer

logger = logging.getLogger(__name__)


class ReplyStepSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Step
        fields = ('id', 'title', 'user', 'status')

    def get_title(self, instance):
        if instance.title == TitleStateChoices.AGREEMENT:
            return instance.user.short_name
        return instance.get_title_display()

    def get_user(self, instance):
        if instance.title == TitleStateChoices.AGREEMENT:
            return UserReplyAvatarSerializer(instance.user, context={'position': instance.get_role_display()}).data
        return None

    def get_status(self, instance):
        if instance.state in (StepStateChoices.EXPECTED, StepStateChoices.STOP):
            return StepStateChoices.EXPECTED
        elif instance.state in (StepStateChoices.END, StepStateChoices.HIDDEN):
            if instance.status == ReplyStatusChoices.CLOSED:
                return StepStateChoices.EXPECTED
            else:
                return instance.status
        elif instance.title == TitleStateChoices.HIRED:  # Неявно состояние шага "активен"
            return ReplyStatusChoices.APPROVED
        else:
            return StepStateChoices.EXPECTED


class ReplyOutboxSerializer(serializers.ModelSerializer):
    date = serializers.DateTimeField(format='%Y-%m-%d', source='created')
    status = serializers.SerializerMethodField()
    vacancy = VacancyShortReplySerializer()
    steps = serializers.SerializerMethodField()
    cancelable = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = Reply
        fields = ('id', 'date', 'status', 'vacancy', 'steps', 'cancelable', 'description')

    def get_status(self, instance):
        return ReplyStatusChoices(instance.status).slug_name_dict

    def get_steps(self, instance):
        steps = instance.steps.all().order_by('index')
        return ReplyStepSerializer(steps, many=True).data

    def get_cancelable(self, instance):
        if instance.status in (
                ReplyStatusChoices.CANCELED,
                ReplyStatusChoices.CLOSED,
                ReplyStatusChoices.REJECTED
        ) or instance.vacancy.status in (VacancyStatusChoices.CLOSED, VacancyStatusChoices.CANCELED):
            return False
        return True

    def get_description(self, instance):
        if instance.status == ReplyStatusChoices.CLOSED:
            return {
                'title': 'Вакансия закрыта',
                'text': None
            }
        elif instance.status == ReplyStatusChoices.REJECTED:
            rejected_step = instance.steps.filter(resolution=StepResolutionChoices.REJECTED).first()
            return {
                'title': 'Причина отказа',
                'text': rejected_step.comment if rejected_step else ''
            }


class ReplyInboxBaseSerializer(serializers.ModelSerializer):
    date = serializers.DateTimeField(format='%Y-%m-%d', source='reply.created')
    status = serializers.SerializerMethodField()
    vacancy = VacancyShortReplySerializer(source='reply.vacancy')
    user = UserReplyAvatarSerializer(source='reply.user')

    class Meta:
        model = Step
        fields = ('id', 'is_viewed', 'date', 'status', 'vacancy', 'user')

    def get_status(self, instance):
        return ReplyStatusChoices(instance.status).slug_name_dict


class ReplyInboxListSerializer(ReplyInboxBaseSerializer):
    my_subordinate = serializers.SerializerMethodField()

    class Meta:
        model = Step
        fields = ReplyInboxBaseSerializer.Meta.fields + ('my_subordinate',)

    def get_my_subordinate(self, instance):
        if instance.role == StepRoleChoices.BOSS:
            return True
        return False


class ReplyInboxSerializer(ReplyInboxBaseSerializer):
    resume = serializers.SerializerMethodField()
    test = serializers.SerializerMethodField()
    experience = serializers.SerializerMethodField()

    class Meta:
        model = Step
        fields = ReplyInboxBaseSerializer.Meta.fields + ('role', 'resume', 'test', 'experience')

    def get_resume(self, instance):
        if instance.reply.resume:
            return instance.reply.resume.url

    def get_test(self, instance):
        if instance.reply.poll and instance.role == StepRoleChoices.NEW_BOSS:
            questions = instance.reply.poll.questions.prefetch_related(
                'user_answer',
                'questiontoanswer_set'
            ).all()  # Все вопросы привязанные к вакансии для конкретного опросника
            return VacancyUserTestSerializer(questions, many=True).data

    def get_experience(self, instance):
        return ExperienceChoices(instance.reply.experience).slug_name_dict


class ReplyInboxUpdateSerializer(serializers.ModelSerializer):
    action = serializers.ChoiceField(choices=StepResolutionChoices.values, source='resolution')
    comment = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = Step
        fields = ('id', 'action', 'comment')

    def validate(self, data):
        action, comment = data.get('resolution'), data.get('comment')
        if action == StepResolutionChoices.REJECTED and not comment:
            raise ValidationError(detail=errors.COMMENT_REQUIRED)
        return data

    def validate_action(self, value):
        step_available_resolution = self.instance.reply.route[self.instance.index]['resolutions']
        if self.instance.state != StepStateChoices.ACTIVE:
            step_available_resolution = {'Нет доступных действий'}
        if value not in step_available_resolution:
            raise ValidationError(detail=errors.action_not_allowed(step_available_resolution))
        return value

    def update(self, instance, validated_data):
        step_end_atr = self.instance.reply.route[self.instance.index]['next'][validated_data.get('resolution')]
        instance.end_activity(
            resolution=validated_data.get('resolution'),
            comment=validated_data.get('comment'),
            **step_end_atr,
        )
        return instance


class ReplyOutboxUpdateSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=[ReplyStatusChoices.CANCELED])

    class Meta:
        model = Reply
        fields = ('id', 'status')

    def validate_status(self, value):
        if self.instance.status in (
                ReplyStatusChoices.CLOSED,
                ReplyStatusChoices.REJECTED
        ) or (self.instance.status == ReplyStatusChoices.HIRED
              and self.instance.vacancy.status == VacancyStatusChoices.CLOSED):
            raise ValidationError(detail=errors.STATUS_INCORRECT)
        return value

    def update(self, instance, validated_data):
        current_step = instance.steps.filter(state=StepStateChoices.ACTIVE).first()
        if current_step and current_step.user != instance.user:
            context = {
                'user': instance.user,
                'vacancy': instance.vacancy,
                'inbox_link': settings.INBOX_LINK
            }
            prepare_and_send_templated_email(
                [current_step.user.email, instance.vacancy.recruiter.email if instance.vacancy.recruiter else None],
                context=context,
                template='email/replies/cancel_reply',
                subject='Карьерные маршруты - Отклик на вакансию отозван.'
            )
            current_step.state = StepStateChoices.END
            current_step.status = ReplyStatusChoices.CANCELED
            current_step.save()
        # Активный шаг завершаем и проставляем ему статус "отозвана"
        # Все шаги до которых процесс еще не дошел переводим в состояние "STOP"
        instance.steps.filter(state=StepStateChoices.EXPECTED).update(state=StepStateChoices.STOP)
        instance.status = ReplyStatusChoices.CANCELED
        instance.save()

        update_reply_resume_status_in_sap.delay(instance.id)
        update_reply_interview_status_in_sap.delay(instance.id)

        # Если вакансия была в статусе "Принят" и больше нет откликов в статусе "Принят",
        # возвращаем вакансию в статус "Опубликована"
        return instance


class OpenAnswerSerializer(serializers.ModelSerializer):
    text = serializers.CharField(source='answer_text')
    is_correct = serializers.SerializerMethodField()

    class Meta:
        model = UserAnswer
        fields = ('id', 'text', 'is_correct')

    def get_is_correct(self, instance):
        return None


class VacancyUserTestSerializer(serializers.ModelSerializer):
    question = serializers.CharField(source='text')
    answer = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ('id', 'question', 'answer')

    def get_answer(self, instance):
        if instance.type != QuestionType.OPEN:
            test_answers = instance.questiontoanswer_set.all()
            result = []
            for test_answer in test_answers:
                result.append(
                    {
                        'id': test_answer.id,
                        'text': test_answer.answer.text,
                        'is_correct': (test_answer.answer.id
                                       in instance.user_answer.all().values_list('answer__id', flat=True))
                        if test_answer.is_correct else None
                    }
                )
            return result
        return [OpenAnswerSerializer(instance.user_answer.first()).data]


class VacancyReplyCreateSerializer(serializers.ModelSerializer):
    vacancy_id = serializers.PrimaryKeyRelatedField(source='vacancy', queryset=Vacancy.objects.all())
    test = serializers.JSONField(source='user.user_answer', write_only=True, required=False)
    experience = serializers.ChoiceField(choices=ExperienceChoices.choices)
    resume = serializers.FileField(required=False)

    class Meta:
        model = Reply
        fields = ('vacancy_id', 'test', 'experience', 'resume', 'comment')

    def validate_vacancy_id(self, value):
        user = self.context['request'].user
        restrict = Restrict.objects.filter(user=user, vacancy_id=value)
        if restrict.exists():
            raise ValidationError(detail=errors.FAILED_TEST)
        reply = Reply.objects.filter(user=user, vacancy_id=value)
        if reply.exists():
            raise ValidationError(detail=errors.DUPLICATE_REPLY)
        if value.status != VacancyStatusChoices.PUBLISHED:
            raise ValidationError(detail=errors.INCORRECT_VACANCY_STATUS)
        return value

    def validate_test(self, value):
        vacancy_id = self.initial_data.get('vacancy_id')
        poll_question_ids = set(Vacancy.objects.get(
            id=vacancy_id
        ).polls.order_by('id').last().questions.values_list('id', flat=True))
        user_question_ids = set(x['question_id'] for x in value)
        if poll_question_ids != user_question_ids:
            raise ValidationError(detail=errors.NOT_ALL_ANSWERS)
        return value

    def validate(self, data):
        if data['vacancy'].selection_type == SelectionTypeChoices.PROFESSIONAL and 'resume' not in data:
            raise ValidationError(detail=errors.RESUME_REQUIRED_ON_PROFESSIONAL_VACANCY)
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        vacancy = validated_data['vacancy']
        if not settings.VACANCY_REPLY_TEST_ENABLED:
            instance = Reply.objects.create(user=user, status=ReplyStatusChoices.PENDING, **validated_data)
            send_candidate_to_sap.delay(instance.id)
            instance.create_steps()
            return instance
        test = validated_data.pop('user').get('user_answer')
        poll = vacancy.polls.order_by('id').last()
        user_test_answers_dict = {}  # Чтобы удобнее было проверять правильность ответов
        extend_answer = []  # Чтобы добавить записи ответов на вопросы, по которым более одного ответа
        for question in test:
            question.update({'user_id': user.id, 'poll_id': poll.id})
            answer = question.pop('answer', None)
            if isinstance(answer, list):
                user_test_answers_dict.update({question['question_id']: set(answer)})
                for ans in answer[1:]:
                    q = question.copy()
                    q.update({'answer_id': ans})
                    extend_answer.append(q)
                question.update({'answer_id': answer[0]})
            elif isinstance(answer, str):
                question.update({'answer_text': answer})
            else:
                raise ValidationError(detail=errors.ANSWER_TYPE_INCORRECT)
        test.extend(extend_answer)
        user_answer_serializer = UserTestAnswerSerializer(data=test, many=True)
        user_answer_serializer.is_valid(raise_exception=True)
        user_answer_serializer.save()
        # Проверка процента правильных
        poll_questions = poll.questions.prefetch_related('questiontoanswer_set').all()
        correct_answer_number = 0
        for question in poll_questions:
            if question.type == QuestionType.OPEN:  # Открытый вопрос, считаем ответ верным.
                correct_answer_number += 1
            else:
                correct_poll_answers = set(
                    question.questiontoanswer_set.filter(is_correct=True).values_list('answer_id', flat=True)
                )
                if correct_poll_answers == user_test_answers_dict.get(question.id):
                    correct_answer_number += 1

        if correct_answer_number / len(poll_questions) < 0.5:  # Если правильных ответов меньше половины
            Restrict.objects.create(vacancy=validated_data['vacancy'], user=user)
            raise ValueError(errors.FAILED_TEST)
        validated_data.update({'user': user, 'status': ReplyStatusChoices.PENDING, 'poll': poll})
        instance = self.Meta.model.objects.create(**validated_data)
        send_candidate_to_sap.delay(instance.id)
        instance.create_steps()
        return instance


class TestDriveDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestDriveDate
        fields = ('date',)


class TestDriveReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = TestDriveReply
        fields = ('date',)

    def validate_date(self, value):
        if not TestDriveDate.objects.filter(date=value).exists():
            raise ValidationError(errors.UNAVAILABLE_DATE)
        return value

    def create(self, validated_data):
        validated_data['user'] = self.context.get('request').user
        test_drive_reply = TestDriveReply.objects.create(**validated_data)
        send_emails_about_new_test_drive_reply.delay(test_drive_reply_id=test_drive_reply.id)
        return test_drive_reply


class VacancyReserveReplySerializer(serializers.ModelSerializer):
    reserve_id = serializers.PrimaryKeyRelatedField(source='vacancy_reserve', queryset=VacancyReserve.objects.all())
    experience = serializers.ChoiceField(choices=ExperienceChoices.choices)

    class Meta:
        model = VacancyReserveReply
        fields = ('reserve_id', 'experience')

    def create(self, validated_data):
        validated_data['user'] = self.context.get('request').user
        vacancy_reserve_reply = VacancyReserveReply.objects.create(**validated_data)
        send_email_about_new_vacancy_reserve_reply.delay(vacancy_reserve_reply.id)
        return vacancy_reserve_reply
