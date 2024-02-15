from django.utils import timezone
from django.utils.datetime_safe import datetime
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from app import errors
from app.settings import EMPLOYEE_CARD_NEW_DAYS
from core.models import CareerType
from core.serializers import BaseCardSerializer
from main.models import (
    Banner,
    CareerTypeCard,
    EmployeeCard,
    InterestingCard,
    Invitation,
    Poll,
    PollResult,
    Question
)


class CareerTypeCardSerializer(BaseCardSerializer):
    type = serializers.SlugField()

    class Meta:
        model = CareerTypeCard
        fields = ['id', 'title', 'description', 'active', 'image', 'type']


class InterestingCardSerializer(BaseCardSerializer):
    class Meta:
        model = InterestingCard
        fields = BaseCardSerializer.Meta.fields + ['id', 'image']


class EmployeeCardSerializer(BaseCardSerializer):
    full_name = serializers.SerializerMethodField()
    is_new = serializers.SerializerMethodField()
    image = serializers.URLField(source='user.image', required=False)

    class Meta:
        model = EmployeeCard
        fields = BaseCardSerializer.Meta.fields + ['id', 'full_name', 'is_new', 'image']

    def get_full_name(self, instance):
        return f"{instance.user.first_name} {instance.user.last_name}"

    def get_is_new(self, instance):
        return timezone.now().date() - instance.modified.date() < timezone.timedelta(days=EMPLOYEE_CARD_NEW_DAYS)


class BannerSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()

    class Meta:
        model = Banner
        fields = ('title', 'text', 'images')

    def get_images(self, instance):
        not_empty_banner_images = instance.banner_images.exclude(user__image_url__isnull=True)
        return [banner_image.user.image_url for banner_image in not_empty_banner_images]


class QuestionSerializer(serializers.ModelSerializer):
    question_id = serializers.CharField(source='id')

    class Meta:
        model = Question
        fields = ('question_id', 'text')


class PollSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True)
    text = serializers.SerializerMethodField()

    class Meta:
        model = Poll
        fields = ('title', 'text', 'questions')

    def get_text(self, instance):
        return instance.text.replace('\\n', '\n')


class MainSerializer(serializers.Serializer):
    career_type_cards = CareerTypeCardSerializer(many=True)
    interesting_cards = InterestingCardSerializer(many=True)
    employee_cards = EmployeeCardSerializer(many=True)
    banner = BannerSerializer()
    poll = PollSerializer()


class CareerTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareerType
        fields = ('slug',)


class PollResultSerializer(serializers.ModelSerializer):
    types = CareerTypeSerializer(source='career_types', many=True)
    text = serializers.SerializerMethodField()

    class Meta:
        model = PollResult
        fields = ('text', 'types')

    def get_text(self, instance):
        return instance.text.replace('\\n', '\n')


class PollAnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    answer = serializers.BooleanField()


class PollAnswerWrapperSerializer(serializers.Serializer):
    answers = PollAnswerSerializer(many=True)


class InvitationSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=EmployeeCard.objects.all())

    def validate(self, data):
        if Invitation.objects.filter(
                sender=self.context.get('request').user,
                recipient=data['id'].user,
                created__day=datetime.now().date().day,
                created__month=datetime.now().date().month,
                created__year=datetime.now().date().year,

        ).exists():
            raise ValidationError(detail=errors.CAREER_AND_COFFEE_INVITE_WRONG_TIME)
        return data

    def create(self, validated_data):
        sender = self.context.get('request').user
        recipient = validated_data['id'].user
        instance = Invitation.objects.create(sender=sender, recipient=recipient)
        instance.send_email()
        return instance
