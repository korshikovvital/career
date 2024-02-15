from rest_framework import serializers

from company.models import City, Office, Position, Unit
from users.models import User
from vacancies.models import VacancyToOffice


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ('id', 'name')


class CityExtendSerializer(serializers.ModelSerializer):
    total_vacancies = serializers.IntegerField()  # Аннотировано.

    class Meta:
        model = City
        fields = ('id', 'name', 'total_vacancies')


class UnitSerializer(serializers.ModelSerializer):
    parent_code = serializers.SerializerMethodField()

    class Meta:
        model = Unit
        fields = ('name', 'code', 'parent_code')

    def get_parent_code(self, instance):
        parent = instance.get_ancestors().last()
        return parent.code if parent else None


class DepartmentSerializer(UnitSerializer):
    total_vacancies = serializers.IntegerField()

    class Meta(UnitSerializer.Meta):
        fields = UnitSerializer.Meta.fields + ('total_vacancies',)


class PositionSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    unit_code = serializers.CharField(source='unit.code')

    class Meta:
        model = Position
        fields = ('id', 'name', 'code', 'unit_code', 'user')

    def get_user(self, instance):
        return {'personnel_number': instance.user_personnel_number, 'full_name': instance.user_full_name}


class PositionInVacancyDescriptionSerializer(PositionSerializer):
    class Meta(PositionSerializer.Meta):
        fields = ('id', 'name', 'selection_type', 'code', 'unit_code')


class OfficeSerializer(serializers.ModelSerializer):
    city = CitySerializer()
    street = serializers.SerializerMethodField()

    def get_street(self, instance):
        return f'{instance.street}, {instance.building}'

    class Meta:
        model = Office
        fields = ('id', 'city', 'street', 'company')


class OfficeInVacancyDescriptionSerializer(OfficeSerializer):
    is_main = serializers.SerializerMethodField()

    class Meta(OfficeSerializer.Meta):
        fields = ('id', 'city', 'street', 'is_main')

    def get_is_main(self, instance):
        return VacancyToOffice.objects.get(office=instance, vacancy=self.context['vacancy']).is_main


class UnitEmployeeSerializer(serializers.Serializer):
    code = serializers.CharField()
    name = serializers.CharField()
    parent_id = serializers.CharField(default=None, allow_null=True)
    manager_id = serializers.CharField(default=None, allow_null=True)

    class Meta:
        fields = ('code', 'parent_id', 'name', 'manager_id')

    def prepare_data(self, data):
        validated_data = data.copy()
        parent_id = validated_data.pop('parent_id', None)
        manager_personnel_number = validated_data.pop('manager_id', None)
        extend_data = {}
        if parent_id:
            parent_obj, _ = Unit.objects.get_or_create(code=parent_id)
            extend_data['parent'] = parent_obj
        if manager_personnel_number:
            manager_obj, _ = User.objects.get_or_create(personnel_number=manager_personnel_number)
            extend_data['manager'] = manager_obj
        validated_data.update(extend_data)
        return validated_data

    def update(self, instance, validated_data):
        data = self.prepare_data(validated_data)
        return super().update(instance, data)

    def create(self, validated_data):
        data = self.prepare_data(validated_data)
        code = data.pop('code')
        instance, created = Unit.objects.update_or_create(
            code=code,
            defaults=data
        )
        self.context.update({'instance_created': created})
        return instance


class PositionEmployeeSerializer(serializers.Serializer):
    code = serializers.CharField()
    name = serializers.CharField()
    unit_id = serializers.CharField(default=None, allow_null=True)

    def prepare_data(self, data):
        validated_data = data.copy()
        unit_id = validated_data.pop('unit_id', None)
        extend_data = {}
        valid = False
        if unit_id:
            unit_obj, _ = Unit.objects.get_or_create(code=unit_id)
            extend_data['unit'] = unit_obj
            valid = True
        validated_data.update(extend_data)
        return validated_data, valid

    def create(self, validated_data):
        data, valid = self.prepare_data(validated_data)
        if valid:
            code = data.pop('code')
            instance, created = Position.objects.update_or_create(code=code, defaults=data)
            self.context.update({'instance_created': created})
            return instance
