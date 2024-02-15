import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from jwt import PyJWTError
from rest_framework.authentication import BaseAuthentication, SessionAuthentication
from rest_framework.exceptions import AuthenticationFailed

from users.tasks import update_user_data

UserModel = get_user_model()


class JWTSSOBackend(BaseAuthentication):

    def authenticate(self, request, **kwargs):
        try:
            prefix, token = request.META[settings.JWT_HEADER_NAME].split(' ', maxsplit=1)
            if prefix != 'Bearer':
                return None

            data = jwt.decode(
                token.encode(),
                settings.JWT_SECRET_KEY,
                algorithms=settings.JWT_ALGORITHMS,
                verify=settings.JWT_CHECK_SECRET_KEY,
                audience=settings.JWT_AUDIENCE,
                options={'verify_signature': settings.JWT_CHECK_SECRET_KEY}
            )

            personnel_number = data.get(settings.JWT_EMPLOYEE_ID)

            if personnel_number is None:
                return None

            user, created = UserModel.objects.get_or_create(
                **{UserModel.USERNAME_FIELD: personnel_number},
            )
            user = self.configure_user(user, **data)
            if created:
                update_user_data.delay(personnel_number=user.personnel_number)

            return user, token

        except (ValueError, KeyError, PyJWTError):
            raise AuthenticationFailed()

    def configure_user(self, user, **kwargs):
        changed = False
        attr_map = {
            settings.JWT_USERNAME: 'username',
            settings.JWT_EMAIL: 'email',
            settings.JWT_FIRST_NAME: 'first_name',
            settings.JWT_LAST_NAME: 'last_name'
        }
        for key, value in attr_map.items():
            if kwargs.get(key) and getattr(user, value) != kwargs.get(key):
                setattr(user, value, kwargs.get(key))
                changed = True
        if changed:
            user.save()
        return user


class CsrfExemptSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening
