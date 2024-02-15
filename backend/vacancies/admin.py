from django.contrib import admin

from vacancies.models import (
    Answer,
    ContestType,
    Factoid,
    Image,
    Poll,
    PollTemplate,
    Question,
    Rate,
    Reason,
    Restrict,
    UserAnswer,
    Vacancy,
    VacancyReserve,
    VacancyType,
    VacancyViewed,
    WorkContract,
    WorkExperience
)


class VacancyImageInline(admin.TabularInline):
    model = Vacancy.images.through
    extra = 0
    verbose_name = 'Фото'
    verbose_name_plural = 'Фото офиса'
    raw_id_fields = ('image',)


class VacancyOfficeInline(admin.TabularInline):
    model = Vacancy.offices.through
    extra = 0
    verbose_name = 'Офис'
    verbose_name_plural = 'Офисы'
    raw_id_fields = ('office',)


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'hot', 'manager_full_name', 'unit', 'status', 'published_by', 'is_referral')
    list_editable = ('hot', 'is_referral')
    ordering = ('title',)
    search_fields = (
        'title', 'manager__personnel_number', 'manager__last_name',
        'published_by__personnel_number', 'published_by__last_name'
    )
    list_filter = ('hot', 'status')
    inlines = (VacancyImageInline, VacancyOfficeInline)
    raw_id_fields = (
        'manager', 'position', 'unit', 'published_by', 'rate', 'vacancy_type',
        'reason', 'work_experience', 'work_contract', 'contest_type', 'recruiter'
    )

    @admin.display(description='Руководитель')
    def manager_full_name(self, obj):
        return obj.manager.full_name if obj.manager else None

    @admin.display(description='Подразделение')
    def unit(self, obj):
        return obj.unit.name if obj.unit else None

    @admin.display(description='Опубликовано')
    def published_by(self, obj):
        return obj.published_by.full_name if obj.published_by else None


@admin.register(VacancyReserve)
class VacancyReserveAdmin(admin.ModelAdmin):
    list_display = ('title', 'direction', 'priority')
    list_editable = ('priority',)


@admin.register(Rate)
class RateAdmin(admin.ModelAdmin):
    list_display = ('title',)


@admin.register(
    WorkExperience,
    VacancyType,
    WorkContract,
    ContestType,
    Reason
)
class SapDictionaryAdmin(admin.ModelAdmin):
    list_display = ('title', 'sap_id')


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    pass


class QuestionAnswerInline(admin.TabularInline):
    model = Question.answers.through
    extra = 0
    verbose_name = 'Ответ'
    verbose_name_plural = 'Ответы'
    raw_id_fields = ('answer',)


class QuestionPollInline(admin.TabularInline):
    model = Question.polls.through
    extra = 0
    verbose_name = 'Опросник'
    verbose_name_plural = 'Опросники'
    raw_id_fields = ('poll',)


class PollQuestionInline(admin.TabularInline):
    model = Poll.questions.through
    extra = 0
    raw_id_fields = ('question',)
    verbose_name = 'Вопрос'
    verbose_name_plural = 'Вопросы'


class PollTemplateQuestionInline(admin.TabularInline):
    model = PollTemplate.questions.through
    extra = 0
    raw_id_fields = ('question',)
    verbose_name = 'Вопрос'
    verbose_name_plural = 'Вопросы'


class QuestionPollTemplateInline(admin.TabularInline):
    model = Question.poll_templates.through
    extra = 0
    verbose_name = 'Шаблон опросника'
    verbose_name_plural = 'Шаблоны опросника'
    raw_id_fields = ('poll_template',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    inlines = (QuestionAnswerInline, QuestionPollInline, QuestionPollTemplateInline)
    search_fields = ('text',)
    list_display = ('text',)


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('text', 'get_questions_text')
    search_fields = ('text',)

    def get_queryset(self, request):
        return super(AnswerAdmin, self).get_queryset(request).prefetch_related('questions')

    @admin.display(description='Вопрос')
    def get_questions_text(self, obj):
        return ', '.join([question.text for question in obj.questions.all()])


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    inlines = (PollQuestionInline,)
    list_display = ('title', 'vacancy')
    raw_id_fields = ('vacancy',)
    search_fields = ('vacancy',)


@admin.register(PollTemplate)
class PollTemplate(admin.ModelAdmin):
    inlines = (PollTemplateQuestionInline,)
    list_display = ('title',)
    search_fields = ('title',)


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    raw_id_fields = ('user', 'poll', 'question', 'answer')


@admin.register(Restrict)
class RestrictAdmin(admin.ModelAdmin):
    raw_id_fields = ('vacancy', 'user')


@admin.register(Factoid)
class FactoidAdmin(admin.ModelAdmin):
    pass


@admin.register(VacancyViewed)
class VacancyViewedAdmin(admin.ModelAdmin):
    pass
