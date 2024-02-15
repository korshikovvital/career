from rest_framework import permissions

from company.models import Unit


class IsHR(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm('users.is_hr')


class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm('users.is_manager') or Unit.objects.filter(manager=request.user).exists()


class IsHeadHR(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm('users.is_head_hr')
