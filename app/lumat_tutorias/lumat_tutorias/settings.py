import sys
from pathlib import Path
from django.templatetags.static import static

import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = 'django-insecure-t_b-)j02g0c-lh&&uh(nbk98upe(gft$*m^qo6h9)7s+2(#e(%'
SECRET_KEY = os.environ.get(
    'SECRET_KEY', 'django-insecure-t_b-)j02g0c-lh&&uh(nbk98upe(gft$*m^qo6h9)7s+2(#e(%')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Application definition

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'lumat_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'lumat_tutorias.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'lumat_tutorias.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER', 'root'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': '3306',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'es-mx'

TIME_ZONE = 'America/Mexico_City'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

UNFOLD = {
    "SITE_TITLE": "Lumat Admin",

    # Logo corregido
    "SITE_LOGO": {
        "light": lambda request: static("logos/lumat.png"),
        "dark": lambda request: static("logos/lumat.png"),
    },

    "COLORS": {
        "primary": {
            "50": "247 244 239",   # #f7f4ef
            "100": "238 232 222",  # #eee8de
            "200": "227 217 203",  # #e3d9cb
            "300": "200 184 154",  # #c8b89a
            "400": "138 117 96",   # #8a7560
            "500": "74 124 122",   # #4a7c7a
            "600": "58 97 95",
            "700": "74 63 50",      # #4a3f32
            "800": "45 38 31",
            "900": "30 25 20",
        },
    },

    "SIDEBAR": {
        "show_search": True,            # Habilita un buscador rápido en el menú
        "show_all_applications": False,

        "navigation": [
            {
                "title": "Control Escolar",
                "separator": True,
                "items": [
                    {
                        "title": "Usuarios",
                        "icon": "group",
                        "link": "/admin/auth/user/",
                    },
                    {
                        "title": "Alumnos",
                        "icon": "school",
                        "link": "/admin/lumat_app/alumno/",
                    },
                    {
                        "title": "Docentes",
                        "icon": "engineering",
                        "link": "/admin/lumat_app/docente/",
                    },
                    {
                        "title": "Comités",
                        "icon": "groups",
                        "link": "/admin/lumat_app/comite/",
                    },
                    {
                        "title": "Seminarios",
                        "icon": "supervised_user_circle",
                        "link": "/admin/lumat_app/seminario/",
                    },
                ],
            },

            {
                "title": "Control administrativo",
                "separator": True,
                "items": [
                    {
                        "title": "Calendario",
                        "icon": "calendar_today",
                        "link": "/admin/calendar-generator/",
                    },
                    {
                        "title": "Estadísticas",
                        "icon": "analytics",
                        "link": "/admin/estadisticas/",
                    },
                ],
            },
        ],
    },

    "STYLES": [
        lambda request: static("css/admin_custom.css"),
    ],
}

CSRF_TRUSTED_ORIGINS = [
    'https://lumat.amer-br.tech',
    'https://www.lumat.amer-br.tech',
]

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

X_FRAME_OPTIONS = "SAMEORIGIN"


# Si el comando ejecutado es 'test', sobreescribimos la base de datos a SQLite en memoria
if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
