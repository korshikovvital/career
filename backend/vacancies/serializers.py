from datetime import timedelta

from django.contrib.auth.models import Permission
from django.db import transaction
from rest_framework import serializers

from app import errors
from company.enums import SelectionTypeChoices
from company.models import City, Office, Position, Unit
from company.serializers import (
    CitySerializer,
    OfficeInVacancyDescriptionSerializer,
    PositionInVacancyDescriptionSerializer,
    UnitSerializer
)
from replies.models import Reply
from sap.tasks import send_extension_vacancy_publication, send_vacancy_to_sap
from users.models import User
from users.serializers import UserReplyAvatarSerializer
from vacancies.enums import VacancyOwnerChoices, VacancyStateChoices, VacancyStatusChoices
from vacancies.models import (
    Answer,
    ContestType,
    Factoid,
    Image,
    Poll,
    PollTemplate,
    Question,
    QuestionToAnswer,
    QuestionToPoll,
    Rate,
    Reason,
    UserAnswer,
    Vacancy,
    VacancyReserve,
    VacancyToOffice,
    VacancyType,
    VacancyViewed,
    WorkContract,
    WorkExperience
)


class VacancyReplyShortSerializer(serializers.ModelSerializer):
    date = serializers.DateTimeField(source='created', format='%d.%m.%Y')

    class Meta:
        model = Reply
        fields = ('id', 'date')


class VacancyTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VacancyType
        fields = ('id', 'title')


class ReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reason
        fields = ('id', 'title')


class WorkContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkContract
        fields = ('id', 'title')


class WorkExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkExperience
        fields = ('id', 'title')


class RateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rate
        fields = ('id', 'title')


class VacancyShortSerializer(serializers.ModelSerializer):
    company_unit_name = serializers.CharField(source='unit.name', allow_null=True)
    manager = UserReplyAvatarSerializer()
    state = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    reply = serializers.SerializerMethodField()
    rate = serializers.SlugRelatedField(slug_field='title', read_only=True)
    replies_count = serializers.IntegerField(source='replies.count')

    class Meta:
        model = Vacancy
        fields = (
            'id', 'title', 'hot', 'is_referral',
            'company_unit_name', 'manager', 'state',
            'status', 'reply', 'rate', 'replies_count'
        )

    def get_state(self, instance: Vacancy):
        user = self.context.get('request').user
        if str(user.top_performer_rate) > str(instance.rate) or not user.top_performer_rate:
            return VacancyStateChoices.RATE_MISMATCH.slug_name_dict
        if user.restrictions.filter(vacancy=instance).exists():  # Завален тест
            return VacancyStateChoices.TEST_FAILED.slug_name_dict
        if user.replies.filter(vacancy=instance).exists():  # Уже откликался
            return VacancyStateChoices.REPLIED.slug_name_dict

        return VacancyStateChoices.REPLY.slug_name_dict

    def get_status(self, instance):
        return VacancyStatusChoices(instance.status).slug_name_dict

    def get_reply(self, instance):
        reply = instance.replies.filter(user=self.context['request'].user).first()
        return VacancyReplyShortSerializer(reply).data if reply else None


class VacancySerializer(VacancyShortSerializer):
    company_units_chain = UnitSerializer(source='unit.chain', many=True)
    images = serializers.SerializerMethodField()
    user_rate = serializers.SerializerMethodField()
    cities = serializers.SerializerMethodField()
    position = PositionInVacancyDescriptionSerializer()
    rate_id = serializers.IntegerField(source='rate.id')
    rate = serializers.CharField(source='rate.title')
    recruiter = UserReplyAvatarSerializer()
    vacancy_type = VacancyTypeSerializer()
    reason = ReasonSerializer()
    work_experience = WorkExperienceSerializer()
    work_contract = WorkContractSerializer()
    release_date = serializers.DateField(format='%d.%m.%Y')
    offices = serializers.SerializerMethodField()
    created = serializers.DateTimeField(format='%d.%m.%Y')

    class Meta(VacancyShortSerializer.Meta):
        fields = (
            'id', 'sap_id', 'created', 'title', 'hot', 'manager', 'state', 'status', 'reply', 'user_rate',
            'duties', 'skills', 'benefits', 'company_units_chain', 'images', 'position', 'rate_id',
            'rate', 'is_referral', 'vacancy_type', 'reason', 'work_experience', 'work_contract', 'release_date',
            'purpose', 'workplace_number', 'kpi', 'comment', 'offices', 'recruiter', 'cities', 'selection_type',
            'replies_count'
        )

    def get_images(self, instance):
        images = instance.images.all()
        return [image.file.url for image in images] if images else []

    def get_user_rate(self, instance):
        return self.context.get('request').user.top_performer_rate

    def get_offices(self, instance):
        return OfficeInVacancyDescriptionSerializer(instance.offices, context={'vacancy': instance}, many=True).data

    def get_cities(self, instance):
        offices = instance.offices.all()
        cities = City.objects.filter(offices__in=offices).distinct()
        return CitySerializer(cities, many=True).data


class VacancyShortReplySerializer(serializers.ModelSerializer):
    company_unit_name = serializers.CharField(source='unit.name', allow_null=True)

    class Meta:
        model = Vacancy
        fields = ('id', 'title', 'company_unit_name')


class OfficeInVacancyCreateUpdateSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Office.objects.all(), source='office')
    is_main = serializers.BooleanField()


class VacancyCreateUpdateSerializer(serializers.ModelSerializer):
    unit_code = serializers.SlugRelatedField(source='unit', queryset=Unit.objects.all(), slug_field='code')
    manager_personnel_number = serializers.SlugRelatedField(
        source='manager', slug_field='personnel_number', queryset=User.objects.all()
    )
    position_id = serializers.PrimaryKeyRelatedField(source='position', queryset=Position.objects.all())
    images = serializers.ListField(child=serializers.FileField(), required=False)
    rate_id = serializers.PrimaryKeyRelatedField(queryset=Rate.objects.all(), source='rate')
    vacancy_type_id = serializers.PrimaryKeyRelatedField(queryset=VacancyType.objects.all(), source='vacancy_type', required=True)
    reason_id = serializers.PrimaryKeyRelatedField(queryset=Reason.objects.all(), source='reason')
    work_experience_id = serializers.PrimaryKeyRelatedField(queryset=WorkExperience.objects.all(), required=True, source='work_experience')
    work_contract_id = serializers.PrimaryKeyRelatedField(queryset=WorkContract.objects.all(), source='work_contract')
    offices = OfficeInVacancyCreateUpdateSerializer(many=True, required=True)
    duties = serializers.CharField(required=True)
    skills = serializers.CharField(required=True)
    benefits = serializers.CharField(required=True)
    workplace_number = serializers.CharField(required=True)
    release_date = serializers.DateField(required=True)
    selection_type = serializers.ChoiceField(choices=SelectionTypeChoices.choices, required=True)
    purpose = serializers.CharField(required=True)

    class Meta:
        model = Vacancy
        fields = (
            'unit_code', 'manager_personnel_number', 'position_id',
            'title', 'rate_id', 'vacancy_type_id', 'reason_id', 'work_experience_id', 'work_contract_id',
            'release_date', 'workplace_number', 'kpi', 'comment', 'duties', 'skills', 'benefits',
            'offices', 'images', 'hot', 'is_referral', 'purpose', 'selection_type'
        )

    def get_end_date(self, validated_data):
        if validated_data.get('hot'):
            end_date = validated_data.get('release_date') + timedelta(weeks=5)
        else:
            end_date = validated_data.get('release_date') + timedelta(weeks=4)
        return end_date

    def validate_offices(self, offices_data):
        main_office = [office for office in offices_data if office['is_main']]
        if len(main_office) != 1:
            raise serializers.ValidationError(detail=errors.MAIN_OFFICE_REQUIRED)
        return offices_data

    def create(self, validated_data):
        publisher = self.context.user
        offices_data = validated_data.pop('offices')
        images = validated_data.pop('images', [])
        end_date = self.get_end_date(validated_data)
        vacancy = Vacancy.objects.create(
            published_by=publisher,
            end_date=end_date,
            status=VacancyStatusChoices.MODERATION,
            contest_type=ContestType.objects.get_default(),
            **validated_data,
        )
        vacancy_to_office = [
            VacancyToOffice(
                vacancy=vacancy,
                office=office_item['office'],
                is_main=office_item['is_main']
            )
            for office_item in offices_data
        ]
        VacancyToOffice.objects.bulk_create(vacancy_to_office)

        if images:
            images = [Image(file=file) for file in images]
            Image.objects.bulk_create(images)
            vacancy.images.set(images)

        # TODO: Если для публикации вакансии тест снова станет обязательным:
        #  - раскомментировать таску send_email_vacancy_without_test
        # Запуск задачи, которая через указанный интервал проверить наличие теста в вакансии
        # Если тест не обнаружится, будет отправлено уведомление на email администраторов.
        # send_email_vacancy_without_test.apply_async((vacancy.id, ), countdown=settings.VACANCY_WITHOUT_TEST_DELAY)
        if vacancy.selection_type == SelectionTypeChoices.PROFESSIONAL:
            send_vacancy_to_sap.delay(vacancy.id)
        return vacancy

    def update(self, instance: Vacancy, validated_data):
        end_date = validated_data.pop('end_date', [])
        images = validated_data.pop('images', [])
        offices = validated_data.pop('offices', [])
        with transaction.atomic():
            if instance.status == VacancyStatusChoices.PUBLISHED:
                validated_data.get('manager', instance.manager).user_permissions.add(
                    Permission.objects.get(codename='is_manager')
                )
            if images:
                images = [Image(file=file) for file in images]
                Image.objects.bulk_create(images)
                # Удаляем старые изображения, чтобы не переполнять хранилку
                instance.images.all().delete()
                instance.images.set(images)
            if offices:
                instance.offices.clear()  # Открепляем старые офисы
                new_offices = [
                    VacancyToOffice(vacancy=instance, office=office_item['office'], is_main=office_item['is_main'])
                    for office_item in offices
                ]
                VacancyToOffice.objects.bulk_create(new_offices)  # Создаем связку с новыми офисами
            super().update(instance, validated_data)
        if end_date:
            send_extension_vacancy_publication.delay(instance.id)
        return instance


class VacancyStatusUpdateSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(
        choices=(
            VacancyStatusChoices.PUBLISHED,
            VacancyStatusChoices.CLOSED
        )
    )

    class Meta:
        model = Vacancy
        fields = ('status',)

    def update(self, instance, validated_data):
        status = validated_data.get('status')
        if status == VacancyStatusChoices.PUBLISHED:
            instance.publish()
        elif status == VacancyStatusChoices.CLOSED:
            instance.close()
        return instance


class VacancyDetailRecruiterUpdateSerializer(VacancyStatusUpdateSerializer):
    recruiter_personnel_number = serializers.SlugRelatedField(
        slug_field='personnel_number',
        source='recruiter',
        queryset=User.objects.all(),
    )

    class Meta(VacancyStatusUpdateSerializer.Meta):
        fields = ('status', 'recruiter_personnel_number')

    def validate_recruiter_personnel_number(self, value):
        if not value.has_perm('users.is_hr'):
            raise serializers.ValidationError(detail=errors.RECRUITER_ROLE_REQUIRED)
        return value

    def update(self, instance, validated_data):
        if 'recruiter' in validated_data:
            instance.recruiter = validated_data.get('recruiter')
            instance.save()
        return super().update(instance, validated_data)


class VacancyReserveSerializer(serializers.ModelSerializer):
    class Meta:
        model = VacancyReserve
        fields = ('id', 'title', 'direction', 'requirements')


class FactoidSerializer(serializers.ModelSerializer):
    url = serializers.CharField(source='file.url')

    class Meta:
        model = Factoid
        fields = ('id', 'url')


class PollRequestAnswerSerializer(serializers.Serializer):
    id = serializers.IntegerField(allow_null=True)
    text = serializers.CharField()
    is_correct = serializers.BooleanField()


class PollRequestQuestionSerializer(serializers.Serializer):
    answers = PollRequestAnswerSerializer(many=True)
    id = serializers.IntegerField(allow_null=True)
    type = serializers.CharField()
    text = serializers.CharField()


class PollRequestSerializer(serializers.Serializer):
    questions = PollRequestQuestionSerializer(many=True)
    title = serializers.CharField()

    def create(self, validated_data):
        vacancy_id = self.context.get('request').parser_context.get('kwargs').get('id')
        poll = Poll.objects.create(
            title=validated_data.pop("title"),
            vacancy_id=vacancy_id
        )
        for question in validated_data.pop("questions"):
            created_question = Question.objects.get_or_create(
                id=question.get("id"),
                text=question.get("text"),
                type=question.get("type"),
            )[0]
            for answer in question.pop("answers"):
                created_answer = Answer.objects.get_or_create(
                    id=answer.get("id"),
                    text=answer.get("text")
                )[0]
                QuestionToAnswer.objects.get_or_create(
                    question=created_question,
                    answer=created_answer,
                    is_correct=answer.get("is_correct")
                )
            QuestionToPoll.objects.create(
                question=created_question,
                poll=poll
            )

        return poll


class PollResponseAnswerSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='answer.id')
    text = serializers.ReadOnlyField(source='answer.text')
    is_correct = serializers.SerializerMethodField(allow_null=True)

    class Meta:
        model = QuestionToAnswer
        fields = ('id', 'text', 'is_correct')

    def get_is_correct(self, instance):
        return None if self.context.get('mode') != 'admin' else instance.is_correct


class PollResponseQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ('id', 'text', 'type', 'answers')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['answers'] = PollResponseAnswerSerializer(
            many=True,
            context=self.context,
            source='questiontoanswer_set'
        )


class PollResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Poll
        fields = ('id', 'title', 'questions')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['questions'] = PollResponseQuestionSerializer(
            many=True,
            context=self.context
        )


class PollTemplateShortInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PollTemplate
        fields = ('id', 'title')


class UserTestAnswerSerializer(serializers.ModelSerializer):
    question_id = serializers.PrimaryKeyRelatedField(queryset=Question.objects.all(), source='question')
    answer_id = serializers.PrimaryKeyRelatedField(queryset=Answer.objects.all(), source='answer', required=False)
    answer_text = serializers.CharField(required=False)
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source='user')
    poll_id = serializers.PrimaryKeyRelatedField(queryset=Poll.objects.all(), source='poll')

    class Meta:
        model = UserAnswer
        fields = ('id', 'question_id', 'answer_id', 'answer_text', 'user_id', 'poll_id')


class MyVacancySerializer(serializers.ModelSerializer):
    created = serializers.DateTimeField(format='%d.%m.%Y')
    status = serializers.SerializerMethodField()
    replies_count = serializers.IntegerField(source='replies.count')
    published_at = serializers.DateField(format='%d.%m.%Y')
    published_by = serializers.CharField(source='published_by.short_name')
    recruiter = serializers.CharField(source='recruiter.short_name', allow_null=True)
    is_new = serializers.BooleanField()  # Добавлено в QS через аннотацию.
    selection_type = serializers.CharField(allow_null=True)

    class Meta:
        model = Vacancy
        fields = ('id', 'sap_id', 'title', 'created', 'hot', 'status', 'replies_count', 'published_at',
                  'published_by', 'recruiter', 'recruiter', 'selection_type', 'is_new', 'is_referral'
                  )

    def get_status(self, instance):
        return VacancyStatusChoices(instance.status).slug_name_dict


class VacancyQueryParamSerializer(serializers.Serializer):
    query = serializers.CharField(required=False)
    status = serializers.ChoiceField(choices=VacancyStatusChoices.choices, required=False)
    owner = serializers.ChoiceField(choices=VacancyOwnerChoices.choices, required=False)
    recruiter_personnel_number = serializers.SlugRelatedField(
        source='recruiter',
        queryset=User.objects.all(),
        slug_field='personnel_number',
        required=False
    )
    status_exclude = serializers.ListField(
        child=serializers.ChoiceField(choices=VacancyStatusChoices.choices), required=False
    )
    selection_type = serializers.ChoiceField(choices=SelectionTypeChoices.choices, required=False)

    def validate_recruiter_personnel_number(self, value):
        if not value.has_perm('users.is_hr'):
            raise serializers.ValidationError(detail=errors.RECRUITER_ROLE_REQUIRED)
        return value


class VacancyPatchRecruiterSerializer(serializers.Serializer):
    vacancies_ids = serializers.ListSerializer(
        child=serializers.PrimaryKeyRelatedField(queryset=Vacancy.objects.all()),
        source='vacancies'
    )
    recruiter_personnel_number = serializers.SlugRelatedField(
        source='recruiter',
        queryset=User.objects.all(),
        slug_field='personnel_number'
    )

    class Meta:
        fields = ('vacancies_ids', 'recruiter_personnel_number')

    def validate_recruiter_personnel_number(self, value):
        if not value.has_perm('users.is_hr'):
            raise serializers.ValidationError(detail=errors.RECRUITER_ROLE_REQUIRED)
        return value

    def save(self, **kwargs):
        user = self.context.get('request').user
        manager_perm = Permission.objects.get(codename='is_manager')
        with transaction.atomic():
            for vacancy in self.validated_data['vacancies']:
                if vacancy.status == VacancyStatusChoices.CLOSED:
                    raise serializers.ValidationError(detail=errors.TRY_CHANGE_CLOSED_VACANCY)
                vacancy.recruiter = self.validated_data['recruiter']
                if vacancy.status == VacancyStatusChoices.MODERATION:
                    vacancy.status = VacancyStatusChoices.PUBLISHED
                vacancy.manager.user_permissions.add(manager_perm)
                VacancyViewed.objects.get_or_create(user=user, vacancy=vacancy)
            Vacancy.objects.bulk_update(self.validated_data['vacancies'], fields=['recruiter', 'status'])
        return
