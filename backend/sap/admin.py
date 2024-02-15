from django.conf import settings
from django.contrib import admin, messages

from .models import SapRequest
from .tasks import create_instances
from .utils import chunks


@admin.register(SapRequest)
class SapRequestAdmin(admin.ModelAdmin):
    list_display = ('guid', 'status', 'endpoint', 'created', 'task')
    list_editable = ('status',)
    search_fields = ('guid', 'status')
    list_filter = ('status',)
    actions = ('create_instances', 'resend_saprequest')

    @admin.action(description='Создать сущности')
    def create_instances(self, request, queryset):

        for sap_request in queryset:
            object_type = sap_request.request_body.get('objectType', '')
            for batch in chunks(sap_request.response_sap.get(object_type, []), settings.SAP_DATA_BATCH_SIZE):
                create_instances.delay(object_type=object_type, data=batch)

    @admin.action(description='Отправить повторно')
    def resend_saprequest(self, request, queryset):
        for sap_request in queryset:
            sap_request.send()
            self.message_user(
                request=request,
                message='Отпоавлены повторно.',
                level=messages.INFO
            )
