from django.contrib import admin
from django.utils import timezone
from django.utils.html import mark_safe

from app.settings import EMPLOYEE_CARD_NEW_DAYS
from main.models import (
    Banner,
    BannerImage,
    CareerTypeCard,
    EmployeeCard,
    InterestingCard,
    Invitation,
    Poll,
    PollResult,
    Question
)


@admin.register(BannerImage)
class BannerImageAdmin(admin.ModelAdmin):
    raw_id_fields = ('user', 'banner')
    list_display = ('image', 'user', 'banner')

    @admin.display(description='Фото сотрудников')
    def image(self, obj):
        if obj.user.image_url:
            height = 100
            width = 100
            return mark_safe(f'<img src="{obj.user.image_url}" width="{width}" height="{height}" />')


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'text')


@admin.register(CareerTypeCard)
class CareerTypeCardAdmin(admin.ModelAdmin):
    list_display = ('title', 'active', 'priority', 'image_to_show')
    list_editable = ('active', 'priority')
    ordering = ('priority',)

    @admin.display(description='Изображение')
    def image_to_show(self, obj):
        height = 100
        width = 100
        return mark_safe(f'<img src="{obj.image.url}" width="{width}" height="{height}" />')


@admin.register(InterestingCard)
class InterestingCardAdmin(admin.ModelAdmin):
    list_display = ('title', 'active', 'priority', 'image_to_show')
    list_editable = ('active', 'priority')
    ordering = ('priority',)

    @admin.display(description='Изображение')
    def image_to_show(self, obj):
        height = 100
        width = 100
        return mark_safe(f'<img src="{obj.image.url}" width="{width}" height="{height}" />')


@admin.register(EmployeeCard)
class EmployeeCardAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'active', 'user', 'is_new', 'image_to_show')
    list_editable = ('active',)
    ordering = ('modified',)
    raw_id_fields = ('user',)

    @admin.display(description='Изображение')
    def image_to_show(self, obj):
        if obj.user.image_url:
            height = 100
            width = 100
            return mark_safe(f'<img src="{obj.user.image_url}" width="{width}" height="{height}" />')

    @admin.display(description='Новая')
    def is_new(self, obj):
        return timezone.now().date() - obj.modified.date() < timezone.timedelta(days=EMPLOYEE_CARD_NEW_DAYS)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'priority', 'career_type', 'poll')
    raw_id_fields = ('poll', )


class PollResultInLine(admin.TabularInline):
    model = PollResult.career_types.through
    extra = 0
    verbose_name = 'Карьерный тип'
    verbose_name_plural = 'К каким карьерным типам относится текущий ответ'


@admin.register(PollResult)
class PollResultAdmin(admin.ModelAdmin):
    inlines = (PollResultInLine,)
    list_display = ('text', 'get_career_types')

    @admin.display(description='Типы карьеры')
    def get_career_types(self, obj):
        return ", ".join([career_type.slug for career_type in obj.career_types.all()])


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    raw_id_fields = ('sender', 'recipient')
    fields = ('sender', 'recipient', 'created')
    readonly_fields = ('created', )
    list_display = ('created', 'sender_full_name', 'recipient_full_name')

    @admin.display(description='Пригласивший')
    def sender_full_name(self, obj):
        return obj.sender.full_name

    @admin.display(description='Приглашенный')
    def recipient_full_name(self, obj):
        return obj.recipient.full_name


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    pass
