import logging
from datetime import timedelta

import environ
from celery.schedules import crontab



env = environ.Env(DEBUG=(bool, False))

SECRET_KEY = 'secret_key'

DEBUG = env('DEBUG')

ALLOWED_HOSTS = ['*']

SERVICE_NAME = env('SERVICE_NAME')

API_BASE = env('API_BASE')
API_VERSION = env('API_VERSION')
API_PREFIX = f'{API_BASE}/{SERVICE_NAME}/{API_VERSION}'
APPEND_SLASH = False

HOST = env('HOST')
PORT = env('PORT')
ENV = env.str('ENV', default='prod')
# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'django_celery_beat',
    'django_prometheus',
    'mptt',
    'django_mptt_admin',
    'mdeditor',

    'app',
    'authentication',
    'users',
    'main',
    'core',
    'vacancies',
    'replies',
    'company',
    'sap'
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

ROOT_URLCONF = 'app.urls'

AUTH_USER_MODEL = 'users.User'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'app.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DATABASE_MASTER_NAME'),
        'USER': env('DATABASE_MASTER_USER'),
        'PASSWORD': env('DATABASE_MASTER_PASSWORD'),
        'HOST': env('DATABASE_HOST'),
        'PORT': env('DATABASE_PORT'),
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/


STATIC_URL = '/static/'
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# JWT параметры
JWT_HEADER_NAME = env.str('JWT_HEADER_NAME', default='HTTP_AUTHORIZATION')
JWT_SECRET_KEY = env.str('JWT_SECRET_KEY', default='').replace('\\n', '\n')
JWT_CHECK_SECRET_KEY = env.bool('JWT_CHECK_SECRET_KEY', default=False)
JWT_ALGORITHMS = env.list('JWT_ALGORITHMS', default=['RS256'])
JWT_AUDIENCE = env.str('JWT_AUDIENCE', default='digital-office')
JWT_EMPLOYEE_ID = env.str('JWT_EMPLOYEE_ID', default='employeeID')
JWT_USERNAME = env.str('JWT_USERNAME', default='preferred_username')
JWT_EMAIL = env.str('JWT_EMAIL', default='email')
JWT_FIRST_NAME = env.str('JWT_FIRST_NAME', default='given_name')
JWT_LAST_NAME = env.str('JWT_LAST_NAME', default='family_name')

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'app.renderers.DataWrappingJSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'authentication.backends.JWTSSOBackend',
        'rest_framework.authentication.BasicAuthentication',
        'authentication.backends.CsrfExemptSessionAuthentication',
    ]
}

# REDIS
REDIS_HOST = env('REDIS_HOST')
REDIS_PORT = env('REDIS_PORT')
REDIS_DB = env('REDIS_DB')

REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# CELERY
CELERY_TASK_ALWAYS_EAGER = env('CELERY_TASK_ALWAYS_EAGER', cast=bool,
                               default=DEBUG)  # by default in debug mode we run all celery tasks in foregroud.
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = False
CELERY_BROKER_URL = REDIS_URL
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_BEAT_SCHEDULE = {
    'check_sap_requests_status': {
        'task': 'sap.tasks.check_sap_requests_status',
        'schedule': timedelta(hours=4),
    },
    'send_interview_notify': {
        'task': 'replies.tasks.send_interview_notify',
        'schedule': crontab(minute=0, hour=3),
    },
    'update_images_for_banner': {
        'task': 'main.tasks.update_images_for_banner',
        'schedule': crontab(day_of_week='0,2,4,6', minute=0, hour=1),
    },
    'update_rates_from_sap': {
        'task': 'sap.tasks.update_rates_from_sap',
        'schedule': crontab(hour=0, minute=0),
    },
    'update_cities_from_sap': {
        'task': 'sap.tasks.update_cities_from_sap',
        'schedule': crontab(hour=1, minute=0),
    },
    'update_addresses_from_sap': {
        'task': 'sap.tasks.update_addresses_from_sap',
        'schedule': crontab(hour=2, minute=0),
    },
    'update_vacancies_types_from_sap': {
        'task': 'sap.tasks.update_vacancies_types_from_sap',
        'schedule': crontab(hour=3, minute=0),
    },
    'update_contests_types_from_sap': {
        'task': 'sap.tasks.update_contests_types_from_sap',
        'schedule': crontab(hour=4, minute=0),
    },
    'update_reasons_from_sap': {
        'task': 'sap.tasks.update_reasons_from_sap',
        'schedule': crontab(hour=5, minute=0),
    },
    'update_work_contracts_from_sap': {
        'task': 'sap.tasks.update_work_contracts_from_sap',
        'schedule': crontab(hour=6, minute=0),
    },
    'update_work_experiences_from_sap': {
        'task': 'sap.tasks.update_work_experiences_from_sap',
        'schedule': crontab(hour=7, minute=0),
    },
    'delete_successful_saprequests': {
        'task': 'sap.tasks.delete_successful_saprequests',
        'schedule': crontab(day_of_month=1, hour=18, minute=0)
    },
    'load_units_data_from_employee': {
        'task': 'company.tasks.load_units_data_from_employee',
        'schedule': crontab(hour=1, minute=30),
    },
    'load_positions_data_from_employee': {
        'task': 'company.tasks.load_positions_data_from_employee',
        'schedule': crontab(hour=1, minute=45),
    },
    'load_users_data_from_employee': {
        'task': 'users.tasks.load_users_data_from_employee',
        'schedule': crontab(hour=2, minute=0),
    },
}

CELERY_TASK_ROUTES = {
    'tasks.tasks.update_cities_from_sap': {'queue': 'heavy'},
    'tasks.tasks.load_users_data_from_employee': {'queue': 'heavy'},
}


# email
EMAIL_ENABLE = env('EMAIL_ENABLE')
EMAIL_SENDER = env('EMAIL_SENDER')
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env('EMAIL_PORT')
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
EMAIL_SUBJECT_PREFIX = env.str('EMAIL_SUBJECT_PREFIX', default='Карьерные маршруты')
REMINDER_INTERVAL = env.int('REMINDER_INTERVAL', default=14)  # Интервал в днях, для отправки напоминаний
MAIN_SITE_LINK = env.str('MAIN_SITE_LINK', default='')
INBOX_LINK = f'{MAIN_SITE_LINK}/{env.str("INBOX_LINK", default="department/reply/inbox")}'
OUTBOX_LINK = f'{MAIN_SITE_LINK}/{env.str("OUTBOX_LINK", default="reply/outbox")}'
HR_VACANCIES_LINK = f'{MAIN_SITE_LINK}/{env.str("HR_VACANCIES_LINK", default="hr/vacancies")}'
# Задержка между созданием и проверкой наличия теста в вакансии
VACANCY_WITHOUT_TEST_DELAY = env.int('VACANCY_WITHOUT_TEST_DELAY', default=30) * 60

# email администраторов
EMAIL_ADMIN = env.str('EMAIL_ADMIN', default='career.routes@megafon.ru')

# email исполнителя заявки на тест-драйв
EMAIL_TEST_DRIVE = env.str('EMAIL_TEST_DRIVE', default='test-drive@megafon.ru')

# email для кадрового резерва
EMAIL_VACANCY_RESERVE = env.str('EMAIL_VACANCY_RESERVE', default='rezerv@megafon.ru')

# количество дней, чтобы показывать бейдж New на карточках "Карьера и кофе"
EMPLOYEE_CARD_NEW_DAYS = env.int('EMPLOYEE_CARD_NEW_DAYS', default=7)

# количество фотографий на баннере на главной странице
NUM_OF_BANNER_IMAGES = env.int('NUM_OF_BANNER_IMAGES', default=22)

# SAP HR
SAP_HR_TECH_USERNAME = env('SAP_HR_TECH_USERNAME', default='')
SAP_HR_TECH_PASSWORD = env('SAP_HR_TECH_PASSWORD', default='')
SAP_HR_BASE_URL = env('SAP_HR_BASE_URL', default='')
SAP_HR_REQUEST_ENDPOINT = env('SAP_HR_REQUEST_ENDPOINT',
                              default='RESTAdapter/CareerRoutes/RequestObject')
SAP_HR_VACANCY_ENDPOINT = env('SAP_HR_VACANCY_ENDPOINT', default='RESTAdapter/CareerRoutes/Vacancy')
SAP_HR_VACANCY_EXTEND_ENDPOINT = env('SAP_HR_VACANCY_EXTEND_ENDPOINT',
                                     default='RESTAdapter/CareerRoutes/VacancyExtend')

SAP_HR_CANDIDATE_ENDPOINT = env('SAP_HR_CANDIDATE_ENDPOINT', default='RESTAdapter/CareerRoutes/Candidate')
SAP_DATA_BATCH_SIZE = env.int('SAP_DATA_BATCH_SIZE', default=25)
SAP_REPLY_REJECT_COMMENT = env('SAP_REPLY_REJECT_COMMENT',
                               default='Отклонено по результатам рассмотрения в системе SAP')
