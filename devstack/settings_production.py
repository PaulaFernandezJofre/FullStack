"""
Django Production Settings - LogicPerfect
========================================
Configuración optimizada para producción con seguridad máxima
"""

from pathlib import Path
from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# =============================================================================
# SEGURIDAD CRÍTICA - PRODUCCIÓN
# =============================================================================

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("DJANGO_SECRET_KEY environment variable is required in production")

DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')
if not ALLOWED_HOSTS or ALLOWED_HOSTS == ['']:
    raise ValueError("ALLOWED_HOSTS environment variable is required in production")

# =============================================================================
# SEGURIDAD - HTTPS y Cookies
# =============================================================================

SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'True') == 'True'
SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', 31536000))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# =============================================================================
# APLICACIONES
# =============================================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    
    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_celery_beat',
    'django_admin_row_actions',
    'social_django',
    
    # Local apps
    'users',
    'core',
    'products',
    'orders',
    'payments',
    'analytics',
    'support',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'devstack.urls'

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
                'core.context_processors.cart_context',
                'core.context_processors.site_settings',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

WSGI_APPLICATION = 'devstack.wsgi.application'

# =============================================================================
# BASE DE DATOS - PostgreSQL (Render)
# =============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'logicperfect'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# =============================================================================
# AUTENTICACIÓN
# =============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTH_USER_MODEL = 'users.User'

AUTHENTICATION_BACKENDS = [
    'users.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]

AUTH_SESSION_COOKIE_AGE = 60 * 60 * 24 * 7
AUTH_SESSION_COOKIE_SECURE = True
AUTH_SESSION_COOKIE_HTTPONLY = True
AUTH_SESSION_COOKIE_SAMESITE = 'Lax'

# =============================================================================
# REST FRAMEWORK - Production
# =============================================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/minute',
        'user': '1000/minute',
        'payments': '30/minute',
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DATETIME_FORMAT': '%Y-%m-%dT%H:%M:%S%z',
    'DATE_FORMAT': '%Y-%m-%d',
    'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler',
}

# =============================================================================
# JWT SETTINGS
# =============================================================================

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}

# =============================================================================
# CORS - Producción
# =============================================================================

CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS']
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# =============================================================================
# CORREO ELECTRÓNICO - SendGrid Free
# =============================================================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = os.getenv('SENDGRID_API_KEY', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'LogicPerfect <noreply@logicperfect.com>')

# =============================================================================
# ALMACENAMIENTO - Static Files con WhiteNoise
# =============================================================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# =============================================================================
# MERCADO PAGO
# =============================================================================

MERCADO_PAGO_ACCESS_TOKEN = os.getenv('MERCADO_PAGO_ACCESS_TOKEN', '')
MERCADO_PAGO_PUBLIC_KEY = os.getenv('MERCADO_PAGO_PUBLIC_KEY', '')
MERCADO_PAGO_ENVIRONMENT = os.getenv('MERCADO_PAGO_ENVIRONMENT', 'sandbox')
MERCADO_PAGO_CHILE_IVA = os.getenv('MERCADO_PAGO_CHILE_IVA', 'False') == 'True'
MERCADO_PAGO_CHILE_IVA_RATE = float(os.getenv('MERCADO_PAGO_CHILE_IVA_RATE', 19))

PLATFORM_COMMISSION_RATE = 0.15
SELLER_COMMISSION_RATE = 0.85

# =============================================================================
# CACHE - LocMem para producción simple
# =============================================================================

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 60 * 15,
    }
}

# =============================================================================
# CONFIGURACIÓN DEL SITIO
# =============================================================================

SITE_NAME = 'LogicPerfect'
SITE_TAGLINE = 'Marketplace de Proyectos de Programación'
SITE_DESCRIPTION = 'Compra y vende software, templates, aplicaciones web, móviles y más.'
SITE_URL = os.getenv('SITE_URL', 'https://logicperfect.com')

SUPPORT_EMAIL = os.getenv('SUPPORT_EMAIL', 'soporte@logicperfect.com')
CONTACT_EMAIL = os.getenv('CONTACT_EMAIL', 'contacto@logicperfect.com')

MIN_WITHDRAWAL_AMOUNT = 50.00
MAX_FILE_SIZE = 100 * 1024 * 1024

# =============================================================================
# INTERNACIONALIZACIÓN
# =============================================================================

LANGUAGE_CODE = 'es'
LANGUAGES = [
    ('es', 'Español'),
    ('en', 'English'),
]

TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =============================================================================
# LOGGING - Producción
# =============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# =============================================================================
# ADMIN
# =============================================================================

CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

ADMIN_SHOW_ALL_PERMS = True
ADMIN_SORTABLE_BY = ['-created_at']

# =============================================================================
# SOCIAL AUTH - Deshabilitado en producción por defecto
# =============================================================================

SOCIAL_AUTH_AVAILABLE = False
