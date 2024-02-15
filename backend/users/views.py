import logging

from django.contrib.auth.models import Permission
from django.db.models import Q
from rest_framework import generics

from company.models import Unit
from users.models import User
from users.serializers import UserQueryParamSerializer, UserShortInfoSerializer

logger = logging.getLogger(__name__)


class UserShortInfoView(generics.RetrieveAPIView):
    serializer_class = UserShortInfoSerializer

    def get_object(self):
        return self.request.user


class UsersListView(generics.ListAPIView):
    serializer_class = UserShortInfoSerializer

    def get_queryset(self):
        query_serializer = UserQueryParamSerializer(data=self.request.query_params)
        query_serializer.is_valid()
        unit_code = query_serializer.validated_data.get('unit_code')
        if query_serializer.validated_data['is_recruiter']:
            perm = Permission.objects.get(codename='is_hr')
            return User.objects.filter(Q(groups__permissions=perm) | Q(user_permissions=perm)).distinct()
        if not unit_code:
            logger.info('unit_code not provided - returning all users')
            return User.objects.all()
        unit = Unit.objects.filter(code=unit_code).first()
        if not unit:
            logger.info(f'Unit with code={unit_code} not found, returning empty queryset')
            return User.objects.none()
        return unit.users_and_managers
