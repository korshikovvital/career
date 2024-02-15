import logging

from rest_framework import serializers

from company.models import City, Position, Unit
from company.serializers import CitySerializer
from users.models import User

logger = logging.getLogger(__name__)


class UserShortInfoSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    city = CitySerializer()
    is_manager = serializers.SerializerMethodField()
    is_hr = serializers.SerializerMethodField()
    is_head_hr = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'personnel_number', 'full_name', 'username', 'email', 'city',
                  'is_staff', 'is_manager', 'is_hr', 'is_head_hr')

    def get_is_manager(self, instance):
        return instance.has_perm('users.is_manager') or Unit.objects.filter(manager=instance).exists()

    def get_is_hr(self, instance):
        return instance.has_perm('users.is_hr')

    def get_is_head_hr(self, instance):
        return instance.has_perm('users.is_head_hr')


class UserEmployeeInfoSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False)
    personnel_number = serializers.CharField(required=True)
    mailbox = serializers.EmailField(source='email', required=False)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    middle_name = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = ['username', 'personnel_number', 'mailbox', 'first_name', 'last_name', 'middle_name']

    def update(self, instance, validated_data):
        validated_data.pop('personnel_number')
        return super().update(instance, validated_data)

    def create(self, validated_data):
        personnel_number = validated_data.pop('personnel_number')
        model_class = self.Meta.model
        instance, created = model_class.objects.update_or_create(
            personnel_number=personnel_number,
            defaults=validated_data
        )
        return instance


class UserAvatarSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='full_name')
    image = serializers.URLField()

    class Meta:
        model = User
        fields = ('personnel_number', 'name', 'image')


class UserReplyAvatarSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True, source='short_name')
    image = serializers.URLField()
    position = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['name', 'image', 'personnel_number', 'position']

    def get_position(self, instance):
        if self.context.get('position'):
            return self.context.get('position')
        return instance.get_position


class UserQueryParamSerializer(serializers.Serializer):
    is_recruiter = serializers.BooleanField(default=False)
    unit_code = serializers.CharField(max_length=20, required=False)


class UserEmployeeShortSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False)
    personnel_number = serializers.CharField(required=True)
    mailbox = serializers.EmailField(source='email', required=False)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    middle_name = serializers.CharField(required=False)
    image = serializers.URLField(source='image_url', required=False)
    hire_date = serializers.DateField(source='hired_at', required=False)
    is_decret = serializers.BooleanField(required=False)
    is_disable = serializers.BooleanField(required=False)
    unit = serializers.CharField(required=False)
    unit_id = serializers.CharField(required=False)
    city = serializers.CharField(required=False)
    position = serializers.CharField(required=False)
    position_id = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = ('username', 'personnel_number', 'mailbox', 'first_name', 'last_name', 'middle_name',
                  'image', 'hire_date', 'is_decret', 'is_disable', 'unit', 'unit_id', 'city', 'position', 'position_id'
                  )

    def prepare_data(self, data):
        validated_data = data.copy()
        unit = validated_data.pop('unit', None)
        unit_id = validated_data.pop('unit_id', None)
        position = validated_data.pop('position', None)
        position_id = validated_data.pop('position_id', None)
        city = validated_data.pop('city', None)
        extend_data = {'is_active': not validated_data.pop('is_disable', True)}
        if unit_id:
            unit_obj, _ = Unit.objects.get_or_create(code=unit_id, defaults={'name': unit})
            extend_data['unit'] = unit_obj
            if position_id:
                position_obj, _ = Position.objects.get_or_create(
                    code=position_id, defaults={'unit': unit_obj, 'name': position}
                )
                extend_data['position'] = position_obj
        if city:
            city_obj, _ = City.objects.get_or_create(name=city)
            extend_data['city'] = city_obj
        validated_data.update(extend_data)
        return validated_data

    def update(self, instance, validated_data):
        validated_data.pop('personnel_number')
        data = self.prepare_data(validated_data)
        return super().update(instance, data)

    def create(self, validated_data):
        personnel_number = validated_data.pop('personnel_number')
        data = self.prepare_data(validated_data)
        model_class = self.Meta.model
        instance, created = model_class.objects.update_or_create(
            personnel_number=personnel_number,
            defaults=data
        )
        self.context.update({'instance_created': created})
        return instance


class UserEmployeeSerializer(UserEmployeeShortSerializer):
    chief = UserEmployeeShortSerializer(source='manager', required=False)

    class Meta(UserEmployeeShortSerializer.Meta):
        fields = UserEmployeeShortSerializer.Meta.fields + ('chief', )

    def prepare_data(self, data):
        validated_data = super().prepare_data(data)
        manager = validated_data.pop('manager', None)
        extend_data = {}
        if manager:
            model_class = self.Meta.model
            manager_instance, created = model_class.objects.get_or_create(
                personnel_number=manager['personnel_number']
            )
            extend_data['manager'] = manager_instance
        validated_data.update(extend_data)
        return validated_data


class UserEmployeeOdataSerializer(serializers.Serializer):
    personnel_number = serializers.CharField()
    updated_at = serializers.DateField()
