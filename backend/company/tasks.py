import logging

from django.contrib.auth import get_user_model
from django.db import transaction

from app.celery import celery
from company.models import InfoFile, Position, Unit
from company.serializers import PositionEmployeeSerializer, UnitEmployeeSerializer
from core.utils import get_employee_data

UserModel = get_user_model()
logger = logging.getLogger(__name__)


@celery.task
def upload_positions_and_units(file_id: int):
    file = InfoFile.objects.get(id=file_id)
    file.parse_positions_and_units()


@celery.task
def load_units_data_from_employee():
    response_data = get_employee_data(url='departments/odata')
    departments_data = response_data.get('data', []) if response_data else []
    if departments_data:
        with transaction.atomic():  # https://django-mptt.readthedocs.io/en/stable/mptt.managers.html#mptt.managers.TreeManager.disable_mptt_updates

            with Unit.objects.disable_mptt_updates():
                serializer = UnitEmployeeSerializer(data=departments_data, many=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
            Unit.objects.rebuild()

        validated_data = serializer.validated_data
        unit_codes = [x['code'] for x in validated_data]
        row = Unit.objects.exclude(
            code__in=unit_codes
        ).filter(
            is_active=True
        ).update(is_active=False)
        logger.info(f'Деактивировано {row} отсутствующих в выгрузке департаментов.')
        row = Unit.objects.deactivate_not_company()
        logger.info(f'Деактивировано {row} департаментов вне дерева МегаФон.')
    else:
        logger.info('Нет данных для обновления.')


@celery.task
def load_positions_data_from_employee():
    response_data = get_employee_data(url='positions')
    positions_data = response_data.get('data', []) if response_data else []
    if positions_data:
        serializer = PositionEmployeeSerializer(data=positions_data, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        validated_data = serializer.validated_data
        position_names = [x['name'] for x in validated_data]
        row = Position.objects.exclude(
            name__in=position_names
        ).filter(
            is_active=True
        ).update(is_active=False)
        logger.info(f'Деактивировано {row} должностей.')
    else:
        logger.info('Нет данных для обновления.')
