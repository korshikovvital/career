import base64
import logging
from collections import OrderedDict
from typing import Tuple

from django.conf import settings
from rest_framework import serializers

from company.enums import SelectionTypeChoices
from company.models import City, Office
from replies.enums import ReplyStatusChoices, StepResolutionChoices, StepStateChoices
from replies.models import Reply, Step
from users.models import User
from vacancies.models import (
    ContestType,
    Rate,
    Reason,
    Vacancy,
    VacancyType,
    WorkContract,
    WorkExperience
)

logger = logging.getLogger(__name__)


class SapGradeSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='title')

    def create(self, validated_data):
        rate, _ = Rate.objects.get_or_create(
            title=validated_data.get('title')
        )
        return rate

    class Meta:
        model = Rate
        fields = ('id',)


class SapCitySerializer(serializers.ModelSerializer):
    textcity = serializers.CharField(source='name')
    idcityhh = serializers.CharField(source='sap_id')

    class Meta:
        model = City
        fields = ('textcity', 'idcityhh')

    def create(self, validated_data):
        name = validated_data.get('name')
        sap_id = validated_data.get('sap_id')
        city, _ = City.objects.update_or_create(
            name=name,
            defaults={'sap_id': sap_id}
        )
        return city


class SapOfficeSerializer(serializers.ModelSerializer):
    idcityhh = serializers.CharField(source='sap_city_id')
    idoffice = serializers.CharField(source='sap_id')
    idcomp = serializers.CharField(source='sap_company_id')
    idfilial = serializers.CharField(source='sap_branch_id')

    class Meta:
        model = Office
        fields = ('idcityhh', 'idoffice', 'idcomp',
                  'idfilial', 'street', 'building')

    def get_text_info_from_ids(self, idcomp: str, idfilial: str) -> Tuple[str, str]:
        id_to_text_map = {
            '01': {
                'textcomp': 'МегаФон',
                'filials': {
                    '1': 'Головной офис',
                    '2': 'Северо-Западный филиал',
                    '3': 'Столичный филиал',
                    '4': 'Кавказский филиал',
                    '5': 'Поволжский филиал',
                    '6': 'Уральский филиал',
                    '7': 'Центральный филиал',
                    '8': 'Сибирский филиал',
                    '9': 'Дальневосточный филиал'
                }
            },
            '02': {
                'textcomp': 'МегаФон Ритейл',
                'filials': {
                    '1': 'Северо-Западный филиал',
                    '2': 'Головной офис',
                    '3': 'Кавказский филиал',
                    '4': 'Столичный филиал',
                    '5': 'Центральный филиал',
                    '6': 'Уральский филиал',
                    '7': 'Поволжский филиал',
                    '8': 'Сибирский филиал',
                    '9': 'Дальневосточный филиал'
                }
            },
            '03': {
                'textcomp': 'Скартел',
                'filials': {
                    '1': 'Головной офис'
                }
            },
            '04': {
                'textcomp': 'МегаЛабс',
                'filials': {
                    '1': 'Головной офис'
                }
            },
            '05': {
                'textcomp': 'NETBYNET',
                'filials': {
                    '1': 'Головной офис'
                }
            },
            '06': {
                'textcomp': 'ТТ-Мобайл',
                'filials': {
                    '1': 'ТТ-Мобайл'
                }
            },
            '07': {
                'textcomp': '"ООО "МегаТех"',
                'filials': {
                    '1': 'Головной офис',
                    '2': 'ОП МегаТех г. Санкт-Петербург',
                    '3': 'ОП МегаТех г. Нижний Новгород',
                    '4': 'ОП МегаТех г. Ростов-на-Дону',
                    '5': 'ОП МегаТех г. Краснодар',
                    '6': 'ОП МегаТех г. Самара',
                    '7': 'ОП МегаТех г. Екатеринбург',
                    '8': 'ОП МегаТех г. Новосибирск',
                    '9': 'ОП МегаТех г. Владивосток',
                    '10': 'ОП МегаТех Вологда Щетинина13',
                    '11': 'ОП МегаТех г. В. Новгород',
                    '12': 'ОП МегаТех Барнаул Ленина154а',
                    '15': 'ОП МегаТех Красноярск Взлетн57',
                    '16': 'ОП МегаТех Томск Мариинский8',
                    '17': 'ОП МегаТех Хабаровск Ленингр9а',
                    '18': 'ОП МегаТех г. Архангельск',
                    '19': 'ОП МегаТех г. Иваново',
                    '20': 'ОП МегаТех г. Калининград',
                    '21': 'ОП МегаТех г. Ярославль',
                    '22': 'ОП МегаТех г. Тверь',
                    '23': 'ОП МегаТех г. Ханты-Мансийск',
                    '24': 'ОП МегаТех г. Уфа',
                    '25': 'ОП МегаТех г. Волгоград',
                    '26': 'ОП МегаТех г. Казань',
                    '27': 'ОП МегаТех г. Нижневартовск',
                    '28': 'ОП МегаТех г. Сургут',
                    '29': 'ОП МегаТех г. Саратов',
                    '30': 'ОП МегаТех г. Пенза',
                    '31': 'ОП МегаТех Брянск Фокина115',
                    '32': 'ОП МегаТех Владимир ВДуброва40',
                    '33': 'ОП МегаТех Тула Михеева15',
                    '34': 'ОП МегаТех Орел МГорького17',
                    '35': 'ОП МегаТех Курск Пар.коммуны73',
                    '36': 'ОП МегаТех Калуга Тульская21а',
                    '37': 'ОП МегаТех Рязань Типанова7',
                    '38': 'ОП МегаТех Иркутск Байкальс108',
                    '39': 'ОП МегаТех Оренбург ЛПопова44',
                    '40': 'ОП МегаТех НабережныеЧелны',
                    '41': 'ОП МегаТех Тольятти Фрунзе6В',
                    '42': 'ОП МегаТех Чита  КраснЗвезды64',
                    '43': 'ОП МегаТех Чебоксары Текстил6',
                    '44': 'ОП МегаТех Воронеж Революци29ж',
                    '45': 'ОП МегаТех в г.Омск',
                    '46': 'ОП МегаТех г.Кемерово'
                }
            }
        }
        return id_to_text_map[idcomp]['textcomp'], id_to_text_map[idcomp]['filials'][idfilial]

    def create(self, validated_data: dict):
        city = City.objects.filter(sap_id=validated_data.get('sap_city_id')).first()
        if city:
            company, branch = self.get_text_info_from_ids(
                idcomp=validated_data.get('sap_company_id'),
                idfilial=validated_data.get('sap_branch_id')
            )
            office, _ = Office.objects.get_or_create(
                city=city,
                sap_city_id=validated_data.get('sap_city_id'),
                sap_company_id=validated_data.get('sap_company_id'),
                sap_branch_id=validated_data.get('sap_branch_id'),
                sap_id=validated_data.get('sap_id'),
                street=validated_data.get('street'),
                building=validated_data.get('building'),
                defaults={**validated_data.update({
                    'company': company,
                    'branch': branch
                })}
            )
            return office
        logger.error(f'City with sap_id {validated_data.get("sap_city_id")} doesn\'t exist! Skip creating office..')

    def to_representation(self, instance):
        return super(SapOfficeSerializer, self).to_representation(instance) if instance else {}


class SapDictionarySerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='sap_id')
    name = serializers.CharField(source='title')

    def create_or_update(self, model, validated_data):
        title = validated_data.get('title')
        sap_id = validated_data.get('sap_id')
        obj, _ = model.objects.update_or_create(
            title=title,
            defaults={'sap_id': sap_id}
        )
        return obj


class WorkExperienceSerializer(SapDictionarySerializer):
    class Meta:
        model = WorkExperience
        fields = ('id', 'name')

    def create(self, validated_data):
        return self.create_or_update(WorkExperience, validated_data)


class WorkContractSerializer(SapDictionarySerializer):
    class Meta:
        model = WorkContract
        fields = ('id', 'name')

    def create(self, validated_data):
        return self.create_or_update(WorkContract, validated_data)


class VacancyTypeSerializer(SapDictionarySerializer):
    class Meta:
        model = VacancyType
        fields = ('id', 'name')

    def create(self, validated_data):
        return self.create_or_update(VacancyType, validated_data)


class ContestTypeSerializer(SapDictionarySerializer):
    class Meta:
        model = ContestType
        fields = ('id', 'name')

    def create(self, validated_data):
        return self.create_or_update(ContestType, validated_data)


class ReasonSerializer(SapDictionarySerializer):
    class Meta:
        model = Reason
        fields = ('id', 'name')

    def create(self, validated_data):
        return self.create_or_update(Reason, validated_data)


class SapVacancySerializer(serializers.ModelSerializer):
    id_career_routes = serializers.CharField(source='id')
    zplans = serializers.StringRelatedField(source='position.code', read_only=True)
    id_typevac = serializers.StringRelatedField(source='vacancy_type.sap_id', read_only=True)
    id_comp = serializers.StringRelatedField(source='contest_type.sap_id', read_only=True)
    empl_start_date = serializers.DateField(source='release_date', format='%Y%m%d', read_only=True)
    reason_code = serializers.StringRelatedField(source='reason.sap_id', read_only=True)
    zzvidrecruit = serializers.SerializerMethodField()
    contract_type = serializers.StringRelatedField(source='work_contract.sap_id', read_only=True)
    end_date = serializers.DateField(format='%Y%m%d', read_only=True)
    zzaddit = serializers.CharField(source='comment')
    zzworkexp = serializers.StringRelatedField(source='work_experience.sap_id', read_only=True)
    zztarget = serializers.CharField(source='purpose')
    task_desc_txt = serializers.CharField(source='duties')
    zzrequir = serializers.CharField(source='skills')
    initiator_personnel_number = serializers.StringRelatedField(source='published_by.personnel_number', read_only=True)
    mainLocation = serializers.SerializerMethodField()
    additionalLocation = serializers.SerializerMethodField()

    class Meta:
        model = Vacancy
        fields = (
            'id_career_routes', 'zplans', 'id_typevac', 'id_comp',
            'empl_start_date', 'reason_code', 'zzvidrecruit', 'contract_type', 'end_date',
            'zzaddit', 'zzworkexp', 'zztarget', 'task_desc_txt', 'zzrequir',
            'initiator_personnel_number', 'mainLocation', 'additionalLocation'
        )

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        final_rep = []
        for key, value in rep.items():
            if value is None:
                value = ""
            elif isinstance(value, dict) and not value:
                continue
            final_rep.append((key, value))
        return OrderedDict(final_rep)

    def get_zzvidrecruit(self, instance):
        return '01' if instance.selection_type == SelectionTypeChoices.PROFESSIONAL else '02'

    def get_mainLocation(self, instance):
        office_to_vacancy = instance.vacancytooffice_set.filter(is_main=True).first()
        if office_to_vacancy:
            data = {
                "zevlt_city": office_to_vacancy.office.city.name if office_to_vacancy.office.city else None,
                "zzoffice": office_to_vacancy.office.sap_id if office_to_vacancy.office else None,
                "zzworkplace": office_to_vacancy.vacancy.workplace_number
            }
        else:
            return {}
        return data

    def get_additionalLocation(self, instance):
        office_to_vacancy = instance.vacancytooffice_set.filter(is_main=False).first()
        if office_to_vacancy:
            data = {
                "zevlt_city": office_to_vacancy.office.city.name if office_to_vacancy.office.city else None,
                "zzoffice": office_to_vacancy.office.sap_id if office_to_vacancy.office else None,
            }
        else:
            return {}
        return data


class SapRecruiterSerializer(serializers.ModelSerializer):
    id_career_routes = serializers.CharField(source='id')
    id_recruiter = serializers.SlugRelatedField(
        source='recruiter',
        slug_field='personnel_number',
        queryset=User.objects.all()
    )
    nb = serializers.CharField(source='sap_id')

    class Meta:
        model = Vacancy
        fields = ('id_career_routes', 'id_recruiter', 'nb')

    def create(self, validated_data):
        vacancy = Vacancy.objects.update_or_create(
            id=int(validated_data.get('id')),
            defaults={
                'recruiter': validated_data.get('recruiter'),
                'sap_id': validated_data.get('sap_id')
            }
        )[0]
        vacancy.publish()
        return vacancy


class SapExtensionPublication(serializers.ModelSerializer):
    id_career_routes = serializers.CharField(source='id')
    nb = serializers.CharField(source='sap_id')

    class Meta:
        model = Vacancy
        fields = ('id_career_routes', 'nb', 'end_date')


class SapReplySerializer(serializers.ModelSerializer):
    id_career_routes = serializers.PrimaryKeyRelatedField(source="vacancy", read_only=True)
    nb = serializers.PrimaryKeyRelatedField(source="vacancy.sap_id", read_only=True)
    pernr = serializers.CharField(source='user.personnel_number', read_only=True)
    created = serializers.DateTimeField(format='%Y%m%d', read_only=True)

    class Meta:
        model = Reply
        fields = ('id_career_routes', 'nb', 'pernr', 'created', 'comment')

    def __init__(self, *args, **kwargs):
        super(SapReplySerializer, self).__init__(*args, **kwargs)

        message_type = self.context.get('message_type')

        self.fields['message_type'] = serializers.CharField(default=message_type, read_only=True)
        self.fields[message_type] = serializers.SerializerMethodField(
            method_name=f'get_{message_type.split("_")[-1]}',
            read_only=True
        )

    def get_feedback(self, instance):
        feedback_info = {
            'appl_date': instance.created.strftime('%Y%m%d'),
            'appl_desc': instance.comment if instance.comment else '',
        }
        if instance.resume:
            feedback_info.update({
                'att_type': instance.resume.name.split('.')[-1],
                'att_header': instance.resume.name.split('/')[-1],
                'attachment': base64.b64encode(instance.resume.read()).decode()
            })
        return feedback_info

    def get_status(self, instance):
        return {
            'status': '0' if
            instance.status == ReplyStatusChoices.REJECTED or instance.status == ReplyStatusChoices.CANCELED
            else '1'
        }


class SapRejectReplySerializer(serializers.ModelSerializer):
    id_career_routes = serializers.CharField()
    nb = serializers.CharField()
    pernr = serializers.CharField()

    class Meta:
        model = Step
        fields = ('id_career_routes', 'nb', 'pernr')

    def save(self, **kwargs):
        assert hasattr(self, '_errors'), (
            'You must call `.is_valid()` before calling `.save()`.'
        )
        assert not self.errors, (
            'You cannot call `.save()` on a serializer with invalid data.'
        )
        validated_data = {**self.validated_data, **kwargs}
        step = Step.objects.select_related(
            'reply', 'reply__user', 'reply__vacancy', 'reply__vacancy__unit'
        ).filter(
            reply__vacancy_id=int(validated_data.get('id_career_routes')),
            reply__user__personnel_number=validated_data.get('pernr'),
            state=StepStateChoices.ACTIVE
        ).first()
        if step:
            step_end_atr = step.reply.route[step.index]['next'][StepResolutionChoices.REJECTED]
            step.end_activity(
                resolution=StepResolutionChoices.REJECTED,
                comment=settings.SAP_REPLY_REJECT_COMMENT,
                **step_end_atr,
            )
        else:
            logger.error(f"Не удалось отклонить отклик на вакансию {validated_data.get('id_career_routes')} "
                         f"(SAP CODE: {validated_data.get('nb')}) "
                         f"сотрудника {validated_data.get('pernr')}."
                         )
        return step


class SapCloseVacancySerializer(serializers.ModelSerializer):
    id_career_routes = serializers.CharField(source='id')
    nb = serializers.CharField(source='sap_id')
    new_status = serializers.ChoiceField(source='status', choices=(2, 3))

    class Meta:
        model = Vacancy
        fields = ('id_career_routes', 'nb', 'new_status')

    def create(self, validated_data):
        vacancy = Vacancy.objects.get(id=validated_data.get('id'))

        if validated_data['status'] == 2:
            vacancy.close()
        elif validated_data['status'] == 3:
            vacancy.cancel()
        return vacancy
