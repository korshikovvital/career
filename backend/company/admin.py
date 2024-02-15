from django.contrib import admin
from django_mptt_admin.admin import DjangoMpttAdmin

from company.models import City, InfoFile, Office, Position, Unit
from company.tasks import upload_positions_and_units


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'sap_id')
    ordering = ('name', 'sap_id')
    search_fields = ('name',)


@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ('id', 'city', 'street', 'sap_id')
    search_fields = ('city__name',)
    raw_id_fields = ('city',)


@admin.register(Unit)
class UnitAdmin(DjangoMpttAdmin):
    raw_id_fields = ('parent', 'manager')
    list_display = ('name', 'code', 'parent_name')
    list_filter = ('level', 'is_active')
    search_fields = ('name', 'code')
    mptt_level_indent = 16

    @admin.display(description='Родительское подразделение')
    def parent_name(self, obj):
        parent = obj.parent
        return parent.name if parent else None


class PositionTargetsInline(admin.TabularInline):
    model = Position.targets.through
    fk_name = 'position'
    verbose_name = 'Целевая должность'
    verbose_name_plural = 'Целевые должности'
    raw_id_fields = ('target',)
    extra = 0


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    raw_id_fields = ('unit',)
    list_display = ('id', 'code', 'name', 'level')
    list_filter = ('level',)
    search_fields = ('name',)
    inlines = (PositionTargetsInline, )


@admin.register(InfoFile)
class InfoFileAdmin(admin.ModelAdmin):
    list_display = ('file', 'created')

    actions = ('upload_positions_and_units',)

    @admin.action(description='Загрузить информацию о должностях и подразделениях')
    def upload_positions_and_units(self, request, queryset):
        upload_positions_and_units.delay(queryset[0].id)
