from typing import List, Tuple, Union

from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from rest_framework.exceptions import (
    AuthenticationFailed,
    ErrorDetail,
    PermissionDenied,
    ValidationError
)
from rest_framework.views import exception_handler

from .errors import DEFAULT_ERROR_CODE
from .responses import (
    BadRequestResponse,
    ForbiddenResponse,
    InternalErrorResponse,
    NotFoundResponse,
    UnauthorizedResponse
)


class ValidationErrorTransformer:

    @staticmethod
    def get_error_type(error_field: str, validation_error: ValidationError) -> str:

        codes_dict = validation_error.get_codes()

        if isinstance(codes_dict[error_field], dict):
            return 'custom_user_error'

        elif isinstance(codes_dict[error_field], list) and isinstance(codes_dict[error_field][0], str):
            return 'simple_field_error'

        else:
            return 'complex_field_error'

    def get_error_detail(
            self,
            error_field: str,
            validation_error: ValidationError
    ) -> Union[ErrorDetail, List[Tuple[int, str, ErrorDetail]]]:

        error_type = self.get_error_type(
            error_field=error_field,
            validation_error=validation_error
        )
        codes_dict = validation_error.get_codes()
        error_details_list = []

        for ind, elem in enumerate(codes_dict[error_field]):
            if error_type == 'simple_field_error':
                if not elem:
                    continue
                error_code = elem
                if error_code and not error_code[-1].isdigit() or not error_code:
                    error_code = DEFAULT_ERROR_CODE
                return ErrorDetail(validation_error.detail[error_field][ind], error_code)

            elif error_type == 'complex_field_error':
                for inner_error_field, error_code in elem.items():
                    error_code = error_code[0]
                    if error_code and not error_code[-1].isdigit() or not error_code:
                        error_code = DEFAULT_ERROR_CODE
                    error_details_list.append(
                        (ind, inner_error_field, ErrorDetail(
                            validation_error.detail[error_field][ind][inner_error_field][0],
                            error_code))
                    )
            else:
                for index in validation_error.detail[error_field].keys():
                    error_code = codes_dict[error_field][index][0]
                    if error_code and not error_code[-1].isdigit() or not error_code:
                        error_code = DEFAULT_ERROR_CODE
                    return ErrorDetail(validation_error.detail[error_field][index][0], error_code)

        return error_details_list


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, ValidationError):
        codes_dict = exc.get_codes()
        error_transformer = ValidationErrorTransformer()
        errors = {}

        for error_field in codes_dict.keys():
            error_details = error_transformer.get_error_detail(
                error_field=error_field,
                validation_error=exc
            )
            errors.update({error_field: error_details if isinstance(error_details, list) else [error_details]})

        response = BadRequestResponse(
            errors=errors
        )
    elif isinstance(exc, AuthenticationFailed):
        response = UnauthorizedResponse
    elif isinstance(exc, PermissionDenied):
        response = ForbiddenResponse
    elif isinstance(exc, (Http404, ObjectDoesNotExist)):
        response = NotFoundResponse

    return response


def handler500(request):
    return InternalErrorResponse
