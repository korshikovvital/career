from django.conf import settings

from app.tests.api_test_case import ApiTestCase


def test_healthcheck():
    test_cls = ApiTestCase()
    health_check_url = f'http://{settings.HOST}:{settings.PORT}/manage/health'
    answer = test_cls.api_get(health_check_url)
    assert answer == {'status': 'UP'}
