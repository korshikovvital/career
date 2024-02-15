from rest_framework.exceptions import ErrorDetail

DEFAULT_ERROR_CODE = 'WDT0001'

FAILED_TEST = 'К сожалению Вы не прошли тестирование, эта вакансия Вам недоступна.'

COMMENT_REQUIRED = {
    'comment': [
        ErrorDetail(
            string='Необходимо указать причину отказа.',
            code='CARE0001'
        )
    ]
}


def action_not_allowed(allowed_action):
    return {
        'action': [
            ErrorDetail(
                string=f'Запрошенное действие недоступно. Доступные действия: {" ".join(allowed_action)}.',
                code='CARE0002'
            )
        ]
    }


STATUS_INCORRECT = {
    'status': [
        ErrorDetail(
            string='На данном этапе отзыв заявки невозможен.',
            code='CARE0003'
        )
    ]
}


NOT_ALL_ANSWERS = {
    'test': [
        ErrorDetail(
            string='Количество ответов не совпадает с количеством вопросов.',
            code='CARE0004'
        )
    ]
}

ANSWER_TYPE_INCORRECT = {
    'answer': [
        ErrorDetail(
            string='Недопустимый тип ответа. Доступно массив из id вариантов ответа или текстовый ответ.',
            code='CARE0005'
        )
    ]
}

INCORRECT_ROLE = {
    'role': [
        ErrorDetail(
            string='Укажите роль из доступных вариантов [manager, hr].',
            code='CARE0006'
        )
    ]
}

DUPLICATE_REPLY = {
    'vacancy_id': [
        ErrorDetail(
            string='У вас уже имеется отклик на указанную вакансию.',
            code='CARE0007'
        )
    ]
}

USER_IS_RESERVED = {
    'user': [
        ErrorDetail(
            string='Ваш руководитель ограничил вам возможность откликаться на вакансии.',
            code='CARE0008'
        )
    ]
}

INCORRECT_INFO_SLUG = {
    'slug': [
        ErrorDetail(
            string='Параметр slug - обязателен и должен быть из списка разделов.',
            code='CARE0009'
        )
    ]
}

INCORRECT_OWNER = {
    'owner': [
        ErrorDetail(
            string='Укажите owner из доступных вариантов [me, other].',
            code='CARE0010'
        )
    ]
}

INCORRECT_ROLE_FOR_FILTERS = {
    'role': [
        ErrorDetail(
            string='Укажите роль из вариантов [manager, hr].',
            code='CARE0011'
        )
    ]
}

UNAVAILABLE_DATE = {
    'date': [
        ErrorDetail(
            string='Выбранной даты нет в списке доступных дат для тест-драйва.',
            code='CARE0012'
        )
    ]
}

INCORRECT_VACANCY_STATUS = {
    'vacancy_id': [
        ErrorDetail(
            string='Откликнуться можно только на вакансию в статусе "Опубликована"',
            code='CARE0013'
        )
    ]
}

CAREER_AND_COFFEE_INVITE_WRONG_TIME = {
    '_global': [
        ErrorDetail(
            string='Ты сегодня уже оставлял заявку на разговор о Карьере и Кофе с данным коллегой, можешь попробовать '
                   'пригласить другого коллегу.',
            code='CARE0014'
        )
    ]
}

MAIN_OFFICE_REQUIRED = {
    'office': [
        ErrorDetail(
            string='Необходимо указать одно основное место работы.',
            code='CARE0015'
        )
    ]
}

RECRUITER_ROLE_REQUIRED = {
    'recruiter_personnel_number': [
        ErrorDetail(
            string='Указанный пользователь не является рекрутером.',
            code='CARE0016'
        )
    ]
}

TRY_CHANGE_CLOSED_VACANCY = {
    'vacancies_ids': [
        ErrorDetail(
            string='Недопустимо внесение изменений в закрытую вакансию.',
            code='CARE0017'
        )
    ]
}

SAP_GUID_NOT_FOUND = {
    'guid': [
        ErrorDetail(
            string='Запрос с таким guid не найден.',
            code='CARE0018'
        )
    ]
}

RESUME_REQUIRED_ON_PROFESSIONAL_VACANCY = {
    'resume': [
        ErrorDetail(
            string='Необходимо приложить резюме для вакансии на проф. подбор.',
            code='CARE0019'
        )
    ]
}
