from django.http import HttpResponse, JsonResponse


class BadRequestResponse(JsonResponse):

    def __init__(self, errors, **kwargs):
        self.data = {
            'errors': {
                field: [{
                    error_attr[0]: [{
                        error_attr[1]: {
                            'message': error_attr[2],
                            'code': error_attr[2].code,
                        }
                    }]
                } if isinstance(error_attr, tuple) else {
                    'message': error_attr,
                    'code': error_attr.code
                } for error_attr in value] for field, value in errors.items()
            }
        }
        super().__init__(self.data, status=400, **kwargs)


HealthcheckResponse = JsonResponse({'status': 'UP'})
NoContentResponse = HttpResponse(status=204)

UnauthorizedResponse = JsonResponse(
    data={
        'errors': {
            '_global': [
                {
                    'code': 'AUTH0001',
                    'message': 'Пользователь не авторизован'
                }
            ]
        }
    },
    status=401
)

ForbiddenResponse = JsonResponse(
    data={
        'errors': {
            '_global': [
                {
                    'code': 'DENY0001',
                    'message': 'Отсутствует доступ к объекту'
                }
            ]
        }
    },
    status=403
)

NotFoundResponse = JsonResponse(
    data={
        "errors": {
            "_global": [
                {
                    "code": "NFND0001",
                    "message": "Запрашиваемый ресурс не найден"
                }
            ]
        }
    },
    status=404
)

InternalErrorResponse = JsonResponse(
    data={
        'errors': {
            '_global': [
                {
                    'code': 'INT0001',
                    'message': 'Что-то пошло не так'
                }
            ]
        }
    },
    status=500
)
