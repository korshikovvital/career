from django.contrib import admin

from core.models import CareerType, CoreFile, Info, Section


@admin.register(CareerType)
class CareerTypeAdmin(admin.ModelAdmin):
    pass


class SectionInline(admin.TabularInline):
    model = Info.sections.through
    extra = 0
    verbose_name = 'Раздел'
    verbose_name_plural = 'Разделы'
    raw_id_fields = ('section',)


@admin.register(Info)
class InfoAdmin(admin.ModelAdmin):
    inlines = (SectionInline,)
    list_display = ('title', 'description', 'priority')
    list_editable = ('priority',)
    ordering = ('priority',)


class InfoToSection(admin.TabularInline):
    model = Section.info.through
    extra = 0
    verbose_name = 'Частый вопрос'
    verbose_name_plural = 'Частые вопросы'
    raw_id_fields = ('info', )


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    inlines = (InfoToSection,)


@admin.register(CoreFile)
class CoreFileAdmin(admin.ModelAdmin):
    pass
