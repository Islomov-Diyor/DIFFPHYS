import os
from pathlib import Path
from decouple import config
import mimetypes
mimetypes.add_type("text/javascript", ".mjs", True)

HF_TOKEN = config("HF_TOKEN")

# Bazaviy katalog (loyihaning ildizi)
BASE_DIR = Path(__file__).resolve().parent.parent

# Xavfsizlik uchun secret key (prod uchun o'zgartir)
SECRET_KEY = 'django-insecure-very-secret-key-change-me'

# Debug rejimi (prod uchun False qil)
DEBUG = True

ALLOWED_HOSTS = []

# Jazzmin va boshqa ilovalar
INSTALLED_APPS = [
    'jazzmin',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'core',
    'users',
    'materials',
    'videos',
    'testsystem',
    'ai_module',
    'docs',
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

ROOT_URLCONF = 'diffphys.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',                # Umumiy templates (agar ishlatsangiz)
            BASE_DIR / 'core' / 'templates',       # ✅ bu sizning core/templates uchun
            BASE_DIR / 'docs' / 'templates',       # (Agar keyin kerak bo‘lsa)
        ],
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

WSGI_APPLICATION = 'diffphys.wsgi.application'

# Database (hozir sqlite ishlatamiz)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Parol siyosati
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

# Til va vaqt zonasi
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'

USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static fayllar sozlamasi
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Production uchun (hozir shart emas, lekin to'g'ri)
STATIC_ROOT = BASE_DIR / 'staticfiles'
# >>> SHU YERGA QO'SHING <<<
TESTS_JSON_DIR = BASE_DIR / "static" / "tests"


# Media fayllar sozlamasi
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'





# Default auto field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your_django_email@gmail.com'
EMAIL_HOST_PASSWORD = 'gmail_app_password'

# PDF'ni shu sayt ichida iframe'da ko'rsatish uchun
X_FRAME_OPTIONS = "SAMEORIGIN"