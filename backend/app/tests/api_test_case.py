from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient


class ApiTestCase(TestCase):

    c = APIClient()

    def get(self, *args, expected=status.HTTP_200_OK, **kwargs):
        method = getattr(self.c, 'get')
        response = method(*args, **kwargs)
        content = response.content

        if isinstance(expected, (tuple, list)):
            assert response.status_code in expected, (content, response.status_code)
        else:
            assert response.status_code == expected, (content, response.status_code)
        return content

    def api_get(self, *args, expected=status.HTTP_200_OK, **kwargs):
        return self._api_call('get', expected, *args, **kwargs)

    def api_post(self, *args, expected=status.HTTP_201_CREATED, format='json', **kwargs):
        return self._api_call('post', expected, format=format, *args, **kwargs)

    def api_put(self, *args, expected=status.HTTP_200_OK, **kwargs):
        return self._api_call('put', expected, *args, **kwargs)

    def api_delete(self, *args, expected=status.HTTP_204_NO_CONTENT, **kwargs):
        return self._api_call('delete', expected, *args, **kwargs)

    def _api_call(self, method, expected, *args, **kwargs):
        method = getattr(self.c, method)
        response = method(*args, **kwargs)
        content = response.json() if len(response.content) else None
        if isinstance(expected, (tuple, list)):
            assert response.status_code in expected, (content, response.status_code)
        else:
            assert response.status_code == expected, (content, response.status_code)

        return content
