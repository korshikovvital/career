import logging

from django.contrib import admin, messages

from replies.models import Reply, Step, TestDriveDate, TestDriveReply, VacancyReserveReply

logger = logging.getLogger(__name__)


class StepsInline(admin.TabularInline):
    model = Step
    extra = 0
    raw_id_fields = ('user', )


@admin.register(Reply)
class ReplyAdmin(admin.ModelAdmin):
    inlines = (StepsInline, )
    raw_id_fields = ('user', 'vacancy', 'poll')
    list_display = ('get_vacancy', 'get_user')
    search_fields = ('vacancy__title', 'user__personnel_number', 'user__last_name')
    actions = ('create_steps', )

    def get_queryset(self, request):
        return Reply.objects.select_related('vacancy', 'user').prefetch_related('steps', 'steps__user').all()

    @admin.display(description='Вакансия')
    def get_vacancy(self, instance):
        return instance.vacancy.title

    @admin.display(description='Соискатель')
    def get_user(self, instance):
        return instance.user.full_name

    @admin.action(description="Сформировать маршрут")
    def create_steps(self, request, queryset):
        logger.info(queryset)
        for instance in queryset:
            created, message = instance.create_steps()
            if created:
                self.message_user(request, message, messages.SUCCESS)
            else:
                self.message_user(request, message, messages.ERROR)


@admin.register(TestDriveReply)
class TestDriveReplyAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'date', 'created')
    search_fields = ('user__personnel_number', 'user__last_name')


@admin.register(TestDriveDate)
class TestDriveDateAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'is_active')
    list_editable = ('is_active',)


@admin.register(VacancyReserveReply)
class VacancyReserveReplyAdmin(admin.ModelAdmin):
    list_display = ('user', 'vacancy_reserve')
    raw_id_fields = ('user', 'vacancy_reserve')

    @admin.display(description='Кадровый резерв')
    def get_vacancy_reserve(self, instance):
        return instance.vacancy_reserve.title

    @admin.display(description='Соискатель')
    def get_user(self, instance):
        return instance.user.full_name
