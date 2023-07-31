"""
Django settings for wlm project.

Generated by 'django-admin startproject' using Django 4.0.4.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

from pathlib import Path
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-02f%bk-#9tr8j$)_)ff&usy-9-c$pgu=r6h1o-rs^%z^+m8dd6"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    "clearcache",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "django_filters",
    "rest_framework",
    "rest_framework_gis",
    "drf_spectacular",
    "corsheaders",
    "django_rq",
    "main",
    "cron_tools",
    "debug_toolbar",
    "authlib",  # for oauth2
    "oauth",  # for oauth2
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "wlm.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "wlm.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": "wlm",
        "USER": "wlm",
        "PASSWORD": "wlm",
        "HOST": "localhost",
        "PORT": "5433",
    }
}
SPATIALITE_LIBRARY_PATH = "/usr/local/lib/mod_spatialite.dylib"


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Europe/Rome"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


LOGGING = {
    "version": 1,  # the dictConfig format version
    "disable_existing_loggers": False,  # retain the default loggers
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "cron": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "django.db.backends": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
}

# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'handlers': {
#         'console': {
#             'level': 'DEBUG',
#             'class': 'logging.StreamHandler',
#         }
#     },
#     'loggers': {
#         'django.db.backends': {
#             'handlers': ['console'],
#             'level': 'DEBUG',
#         },
#     }
# }

REST_FRAMEWORK = {
    # YOUR SETTINGS
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        #"rest_framework.authentication.SessionAuthentication",
    ],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=24),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Your Project API",
    "DESCRIPTION": "Your project description",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # OTHER SETTINGS
    "SWAGGER_UI_SETTINGS": {
        "syntaxHighlight": False,
    },
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379",
    },
    "views": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379",
    },
}

RQ_QUEUES = {
    "default": {
        "HOST": "localhost",
        "PORT": 6379,
        "DB": 1,
    },
}

RQ_SHOW_ADMIN_LINK = True

CRON_JOB_HANLDERS = {
    "take_snapshot": "main.job_handlers.enqueue_take_snapshot",
    "take_snapshot_reset_pics": "main.job_handlers.enqueue_take_snapshot_reset_pics",
}

CORS_ALLOW_ALL_ORIGINS = True


INTERNAL_IPS = [
    "127.0.0.1",
]

# override in localsettings to enable caching with last-modified header
HTTP_CONDITIONAL_CACHE = False

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# import os
# # Create a LOGGING dictionary
# LOGGING = {
#     # Use v1 of the logging config schema
#     'version': 1,
#     # Continue to use existing loggers
#     'disable_existing_loggers': False,
#     # Create a log handler that prints logs to the terminal
#     'handlers': {
#         'console': {
#             'class': 'logging.StreamHandler',
#         },
#     },
#     # Define the root logger's settings
#     'root': {
#         'handlers': ['console'],
#         'level': 'DEBUG',
#     },
#     # Define the django log module's settings
#     'loggers': {
#         'django': {
#             'handlers': ['console'],
#             'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
#             'propagate': False,
#         },
#     },
# }

WIKIMEDIA_BASE_URL = "http://wlm.inmagik.com:8080"
URL_ACTION_API = f"{WIKIMEDIA_BASE_URL}/api.php"
URL_AUTH_API = f"{WIKIMEDIA_BASE_URL}/rest.php/oauth2"
URL_FRONTEND = "http://localhost:5173/it/"

WIKIMEDIA_CLIENT_ID = "62c6d557e5a4fc319e30321d7504d02d" # "bc5f72672241aba79454db0aa6dc93c5"
WIKIMEDIA_CLIENT_SECRET = "fed8821fff238d1eb0707f0d755ebf63467da214" # "37fb4729f149b41505305eb518d818962fe47fed"


try:
    from .localsettings import *  # type: ignore
except ImportError:
    pass
