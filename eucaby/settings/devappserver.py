
from eucaby.settings.base import *  # pylint: disable=wildcard-import

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'eucaby',
        'USER': 'dev',
        'PASSWORD': 'devpass',
        'HOST': '',
        'PORT': '',
    }
}