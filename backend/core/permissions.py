from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS, IsAdminUser


class ReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method not in SAFE_METHODS:
            return False
        return True


class ObjectOwnerOrAdminUser(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or IsAdminUser().has_permission(request, view)
