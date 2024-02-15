import logging

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from users.models import User

logger = logging.getLogger(__name__)


@admin.register(User)
class UserAdmin(UserAdmin):
    search_fields = ('last_name', 'first_name', 'middle_name', 'email', 'username', 'personnel_number')
    list_display = ('personnel_number',) + UserAdmin.list_display + ('groups_list',)
    list_filter = ('is_active', 'is_staff', 'groups')
    raw_id_fields = ("city", "unit", "position", "manager")
    actions = ('update_from_employee', )
    fieldsets = (
        (None, {"fields": ("personnel_number", "username", "password")}),
        (_("Personal info"), {"fields": (
            "first_name", "last_name", "middle_name", "email", "image_url", "custom_image_url", "city", "hired_at", "fired_at", "is_decret"
        )}),
        ("Штатное расписание", {"fields": ("unit", "manager", "position")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("personnel_number", "password1", "password2"),
            },
        ),
    )

    @admin.display(description='Обновить данные пользователя')
    def update_from_employee(self, request, queryset):
        for user in queryset:
            error = user.update_from_employee()
            if error:
                self.message_user(request, error, messages.ERROR)
            else:
                self.message_user(request, f'Данные {user.personnel_number} обновлены', messages.SUCCESS)

    @admin.display(description='Группы')
    def groups_list(self, obj):
        return [group.name for group in obj.groups.all()]
