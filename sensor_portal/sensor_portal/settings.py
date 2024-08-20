"""
Django settings for sensor_portal project.

Generated by 'django-admin startproject' using Django 4.0.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

import os
from pathlib import Path
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
MEDIA_ROOT = os.path.abspath('/media/file_storage')
MEDIA_URL = 'media/'

FILE_STORAGE_ROOT = '/media/file_storage'
FILE_STORAGE_URL = 'storage/'

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-c-=p42@cm%8sy6-49_32*1g31eh*_w^nj)is51-%$m49zwkvm7'

if os.environ.get('DEV') is not None or platform.system() == "Windows":
    print("Running in dev mode")
    DEBUG = True
    STATIC_URL = 'static/'
    STATICFILES_DIRS = [
        os.path.join(BASE_DIR, 'static_files'),
    ]
    STATIC_ROOT = os.path.join(BASE_DIR, 'static')
    CORS_ALLOW_ALL_ORIGINS = True

ALLOWED_HOSTS = []

print("Reading settings!")

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'django_filters',
    'django.contrib.postgres',
    "rest_framework",
    "rest_framework_gis",
    "rest_framework.authtoken",
    # celery
    'django_celery_results',
    'django_celery_beat',
    # additional extensions
    'bridgekeeper',
    'debug_toolbar',
    'corsheaders',
    'rest_framework_simplejwt.token_blacklist',
    # my apps
    'data_models',
    'user_management',
    'utils'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',

]

ROOT_URLCONF = 'sensor_portal.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, "templates")],
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

WSGI_APPLICATION = 'sensor_portal.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    'default': {
        # 'ENGINE': 'django.db.backends.postgresql',
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.environ.get('POSTGRES_NAME'),
        'USER': os.environ.get('POSTGRES_USER'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
        'HOST': 'sensor_portal_db',
        'PORT': 5432,
    }
}
AUTH_USER_MODEL = "user_management.User"

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'bridgekeeper.backends.RulePermissionBackend',
)

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

USE_L10N = False  # allow use of custom datetime formats
DATE_FORMAT = "Y-m-d"
DATETIME_FORMAT = 'c'
TIME_FORMAT = "H:i:s e"
SHORT_DATETIME_FORMAT = 'Y-n-j G:i:s'


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/


# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': ['bridgekeeper.rest_framework.RuleFilter',
                                'django_filters.rest_framework.DjangoFilterBackend',
                                'rest_framework.filters.SearchFilter'],
    'DEFAULT_PERMISSION_CLASSES': (
        'bridgekeeper.rest_framework.RulePermissions',
    ),
    'DEFAULT_PAGINATION_CLASS': 'utils.paginators.VariablePagePaginator',
    'PAGE_SIZE': 1,
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication'
    ],
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        # 'rest_framework.renderers.BrowsableAPIRenderer'
        'utils.api.BrowsableAPIRendererWithoutForms',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=10),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get("CELERY_BROKER", "redis://redis:6379/0")
    }
}

CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER", "redis://redis:6379/0")
# os.environ.get("CELERY_BROKER", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = 'django-db'
CELERY_RESULT_EXTENDED = True


CELERY_TASK_DEFAULT_QUEUE = 'main_worker'

CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = False

CELERY_BEAT_SCHEDULE = {}

# SENSOR-PORTAL SETTINGS
# name of the global project all deployments will be added to
GLOBAL_PROJECT_ID = "GLOBAL"
