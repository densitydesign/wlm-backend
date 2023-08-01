DEBUG = False
ALLOWED_HOSTS = ['*']

STATIC_ROOT = '/data/statik'

MEDIA_ROOT = '/data/media'

MEDIA_URL = '/media/'

STATIC_URL = '/statik/'

X_FRAME_OPTIONS = 'SAMEORIGIN'

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': "wlm",
        'USER': "wlm",
        'PASSWORD': "wlm",
        'HOST': "wlm_db",
        'PORT': "5432",
        'CONN_MAX_AGE': 600,
    }

}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://wlm_redis:6379',
    },
    'views': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://wlm_redis:6379',
    }
}

RQ_QUEUES = {
    'default': {
        'HOST': 'wlm_redis',
        'PORT': 6379,
        'DB': 1,
    },
}

HTTP_CONDITIONAL_CACHE = True

URL_AUTH_API = "http://wlm.inmagik.com:8080/rest.php/oauth2"
URL_FRONTEND = "https://wlm.inmagik.com/it/"

WIKIMEDIA_CLIENT_ID = "b5b68ee3e6e6c301b6536505b245541e"
WIKIMEDIA_CLIENT_SECRET = "4c8bf075e52b543a445368860b7524b6bfe85938"