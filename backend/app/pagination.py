from django.conf import settings
from django.http import JsonResponse
from rest_framework.pagination import LimitOffsetPagination


class DataWrappingLimitOffsetPagination(LimitOffsetPagination):
    default_limit = settings.DEFAULT_PAGINATION_LIMIT

    def get_paginated_response(self, data):
        return JsonResponse({
            'pagination': {
                'total': self.count,
                'offset': self.offset,
            },
            'data': data
        })
