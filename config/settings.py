"""
Django settings for AIFlow project.
Smart configuration using environment variables for security and flexibility.
"""

import os
from pathlib import Path
from decouple import config

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

# Railway-friendly ALLOWED_HOSTS configuration
ALLOWED_HOSTS_ENV = config('ALLOWED_HOSTS', default='localhost,127.0.0.1')
if ALLOWED_HOSTS_ENV == '*':
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = [s.strip() for s in ALLOWED_HOSTS_ENV.split(',')]

# Add Railway domain automatically
RAILWAY_STATIC_URL = config('RAILWAY_STATIC_URL', default='')
if RAILWAY_STATIC_URL:
    railway_domain = RAILWAY_STATIC_URL.replace('https://', '').replace('http://', '')
    if railway_domain and railway_domain not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(railway_domain)

# Add .railway.app domains
if not any(host.endswith('.railway.app') or host == '*' for host in ALLOWED_HOSTS):
    ALLOWED_HOSTS.append('.railway.app')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'corsheaders',
    'drf_spectacular',
    
    # Local apps
    'apps.core',
    'apps.users',
    'apps.api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='aiflow_db'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres'),
        'HOST': config('DB_HOST', default='db'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# CORS Configuration - Smart handling for development and production
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000',
    cast=lambda v: [s.strip() for s in v.split(',')]
)
CORS_ALLOW_CREDENTIALS = True

# Auto-add Vercel deployment URLs
# Vercel preview deployments follow pattern: *-git-*.vercel.app or *.vercel.app
if not DEBUG:
    # Allow all Vercel domains in production (or configure specific domain in env)
    vercel_domain = config('VERCEL_URL', default='')
    if vercel_domain:
        vercel_origin = f'https://{vercel_domain}' if not vercel_domain.startswith('http') else vercel_domain
        if vercel_origin not in CORS_ALLOWED_ORIGINS:
            CORS_ALLOWED_ORIGINS.append(vercel_origin)
    
    # Also add production frontend domain if specified
    frontend_url = config('FRONTEND_URL', default='')
    if frontend_url and frontend_url not in CORS_ALLOWED_ORIGINS:
        CORS_ALLOWED_ORIGINS.append(frontend_url)

# Celery Configuration
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://redis:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://redis:6379/0')
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# API Documentation
SPECTACULAR_SETTINGS = {
    'TITLE': 'AIFlow API',
    'DESCRIPTION': 'Smart API for AIFlow application',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}
