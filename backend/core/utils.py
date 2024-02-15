import json
import logging
import random
from typing import Union

import httpx
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from httpx import HTTPError, Timeout

logger = logging.getLogger(__name__)


def get_employee_data(url: str, params={}) -> Union[dict, None]:
    url = f'{settings.EMPLOYEE_BASE_API_URL}/{url}'
    timeout = Timeout(120.0, connect=5.0)
    try:
        response = httpx.get(
            url=url,
            params=params,
            auth=(settings.EMPLOYEE_TECH_USER, settings.EMPLOYEE_TECH_PASSWORD),
            timeout=timeout,
            verify=False
        )
        if response.status_code == 200:
            return json.loads(response.content)
        else:
            logger.error(f"Request to {url} failed with status: {response.status_code}")
    except HTTPError:
        logger.error(f'Error with sending request to {url}')
    return None


def file_path(instance, filename):
    content_type = ContentType.objects.get_for_model(instance)
    prefix = timezone.now().strftime('%Y%m%d_%H%M%S') + '_' + str(random.randint(1, 1000000))
    return f'{content_type.app_label}/{content_type.model}/{prefix}_{filename}'
