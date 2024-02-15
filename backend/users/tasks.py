import logging

import httpx
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone

from app.celery import celery
from core.utils import get_employee_data
from users.serializers import UserEmployeeOdataSerializer, UserEmployeeSerializer

UserModel = get_user_model()
logger = logging.getLogger(__name__)


@celery.task
def update_user_data(personnel_number):
    user = UserModel.objects.get(personnel_number=personnel_number)
    user.update_from_employee()


def is_image_exists(employee_image_url):
    """Проверяет существование фото пользователя.
    Сейчас фото пользователей хранятся на разных хостах для dev и prod сервиса emply.
    Если у пользователя нет фото - код ошибки:
    https://dm.msk-cicd-s3.megafon.ru (dev) - 403
    https://cdn.meganet.megafon.ru (prod) - 404
    """
    try:
        response = httpx.get(url=employee_image_url, verify=False)

        if response.status_code == 200:
            logger.info(f'Image exists for url {employee_image_url}.')
            return True

        elif response.status_code in (403, 404):
            logger.info(f'Image not found for url {employee_image_url}.')

        return False

    except Exception as e:
        logger.error(f'Request error for image check for url {employee_image_url}: {e}')
        return False


@celery.task
def load_users_data_from_employee():
    last_update = cache.get(settings.USERS_LAST_UPDATE_CACHE_KEY)
    filter_ = settings.USERS_EMPLOYEE_FILTER
    new_last_update = timezone.now().date()
    skip = 0
    top = settings.EMPLOYEE_CHUNK_SIZE
    not_fired_users_personnel_numbers = []
    error_count = 0
    while True:
        data = get_employee_data(
            url='employees/odata_v2', params={'filter': filter_, 'top': top, 'skip': skip}
        )
        if data is None:
            raise Exception(
                'Не удалось получить данные об изменениях пользователей с employee.'
                f'Праметры: url: employees/odata_v2, filter: {filter_}, top: {top}, skip: {skip}.'
            )
        if not data.get('data'):
            break
        for employee_data in data['data']:
            serializer_odata = UserEmployeeOdataSerializer(data=employee_data)
            if serializer_odata.is_valid():
                personnel_number = serializer_odata.validated_data['personnel_number']
                updated_at = serializer_odata.validated_data['updated_at']
                not_fired_users_personnel_numbers.append(personnel_number)
                if not last_update or updated_at >= last_update:
                    data = get_employee_data(url='employee', params={"pn": personnel_number})
                    if data is None:
                        logger.info(f'На запрос данных о {personnel_number} получен пустой ответ.')
                        error_count += 1
                        if error_count >= settings.USER_LOAD_MAX_ERROR:
                            raise Exception(f'Получен {error_count} раз подряд пустой ответ.')
                    elif data.get('data'):
                        error_count = 0
                        serializer = UserEmployeeSerializer(data=data.get('data'))
                        if serializer.is_valid():
                            serializer.validated_data['image_url'] = (
                                serializer.validated_data['image_url'] if is_image_exists(serializer.validated_data['image_url']) else None
                            )
                            serializer.save()
                        else:
                            logger.info(
                                f'Данные по пользователю {personnel_number} не прошли валидацию. Ошибка: {serializer.errors}'
                            )
            else:
                error_count += 1
                if error_count >= settings.USER_LOAD_MAX_ERROR:
                    raise Exception(f'Получено {error_count} ошибок подряд, что превышает максимальное число ошибок.')
        skip += top
    cache.set(settings.USERS_LAST_UPDATE_CACHE_KEY, new_last_update, timeout=None)
    # увольняем тех кого не было в выгрузке
    current_users_count = UserModel.objects.filter(is_active=True).exclude(is_superuser=True).exclude(is_staff=True).count()
    need_to_fired = UserModel.objects.filter(is_active=True).exclude(is_superuser=True).exclude(is_staff=True).exclude(
        personnel_number__in=not_fired_users_personnel_numbers
    ).count()
    percent_users_to_fired = need_to_fired * 100 / current_users_count
    if percent_users_to_fired <= settings.MAX_PERCENT_OF_USER_TO_BE_FIRED:
        # Увольняем если только надо уволить меньше установленного процента пользователей. Защита, если выгрузка не полная.
        fired_count = UserModel.objects.filter(is_active=True).exclude(is_superuser=True).exclude(is_staff=True).exclude(
            personnel_number__in=not_fired_users_personnel_numbers
        ).update(modified=timezone.now(), fired_at=timezone.now(), is_active=False)
        logger.info(f'Уволено {fired_count} пользователей.')
    else:
        logger.info(
            f'Превышен максимально допустимый процент пользователей к увольнению. Необходимо уволить {percent_users_to_fired}%'
        )
