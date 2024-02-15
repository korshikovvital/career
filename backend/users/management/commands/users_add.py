from django.core.management.base import BaseCommand

from core.utils import get_employee_data
from users.models import User
from users.serializers import UserEmployeeInfoSerializer


class Command(BaseCommand):
    help = 'Добавление пользователей по списку табельных номеров ' \
           'Табельные номера указываем в качестве аргументов разделенных пробелом. ' \
           'Пример: users_add 54002426 22007103.'

    def add_arguments(self, parser):
        parser.add_argument('personnel_numbers', nargs='+', type=str)

    def handle(self, *args, **options):
        for personnel_number in options['personnel_numbers']:
            employee_data = get_employee_data(url='employee', params={"pn": personnel_number})
            if employee_data:
                serializer = UserEmployeeInfoSerializer(data=employee_data['data'])
                if serializer.is_valid():
                    user_data = serializer.validated_data
                    personnel_number = user_data.pop('personnel_number')
                    user, created = User.objects.update_or_create(
                        personnel_number=personnel_number, defaults=user_data
                    )
                    if created:
                        self.stdout.write(f'Пользователь {user.personnel_number}, {user.full_name} создан')
                    else:
                        self.stdout.write(
                            f'Пользователь {user.personnel_number}, {user.full_name} '
                            'уже имеется в системе, его данные были обновлены.'
                        )
                else:
                    self.stdout.write(self.style.NOTICE(
                        f'Данные по сотруднику {personnel_number} были получены, но они не прошли валидацию.\n'
                        f'Ошибки валидации: {serializer.errors}.\n'
                        f'Полученные данные: {employee_data["data"]}'
                    ))
            else:
                self.stdout.write(self.style.NOTICE(f'Данные по {personnel_number} не найдены.'))
        self.stdout.write(self.style.SUCCESS('Users import end'))
