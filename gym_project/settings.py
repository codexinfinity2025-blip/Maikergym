import os
from pathlib import Path
from decouple import config
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = config('DEBUG', default=True, cast=bool)

SECRET_KEY = config(
    'SECRET_KEY',
    default='django-insecure-local-development-key',
)

if not DEBUG and SECRET_KEY.startswith('django-insecure-'):
    raise ImproperlyConfigured(
        'Debes configurar una SECRET_KEY segura antes de iniciar producción.'
    )


def config_list(nombre, default=''):
    """Convierte una variable separada por comas en una lista limpia."""
    valor = config(nombre, default=default)
    return [elemento.strip() for elemento in valor.split(',') if elemento.strip()]


ALLOWED_HOSTS = config_list('ALLOWED_HOSTS', 'localhost,127.0.0.1')
CSRF_TRUSTED_ORIGINS = config_list('CSRF_TRUSTED_ORIGINS')

# Railway publica estas variables automáticamente cuando se genera el dominio.
railway_public_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', '').strip()
if railway_public_domain:
    ALLOWED_HOSTS.append(railway_public_domain)
    CSRF_TRUSTED_ORIGINS.append(f'https://{railway_public_domain}')

# El healthcheck usa un host interno diferente al dominio público.
if 'healthcheck.railway.app' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('healthcheck.railway.app')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'gym_project.gym_app.apps.GymAppConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gym_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'gym_project/gym_app/templates')],
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

WSGI_APPLICATION = 'gym_project.wsgi.application'

MYSQL_DATABASE = config(
    'MYSQL_DATABASE',
    default=config('MYSQLDATABASE', default=''),
)

if MYSQL_DATABASE:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': MYSQL_DATABASE,
            'USER': config(
                'MYSQL_USER',
                default=config('MYSQLUSER', default='root'),
            ),
            'PASSWORD': config(
                'MYSQL_PASSWORD',
                default=config('MYSQLPASSWORD', default=''),
            ),
            'HOST': config(
                'MYSQL_HOST',
                default=config('MYSQLHOST', default='127.0.0.1'),
            ),
            'PORT': config(
                'MYSQL_PORT',
                default=config('MYSQLPORT', default='3306'),
            ),
            'CONN_MAX_AGE': 600,
            'CONN_HEALTH_CHECKS': True,
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

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

LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'gym_project/gym_app/static']

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = Path(
    config(
        'MEDIA_ROOT',
        default=os.environ.get('RAILWAY_VOLUME_MOUNT_PATH', BASE_DIR / 'media'),
    )
)

if not DEBUG:
    # Railway termina HTTPS en su proxy y Django recibe este encabezado.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    # El sondeo interno de Railway llega por HTTP. Solo esta ruta queda exenta
    # para que el healthcheck responda 200 sin desactivar HTTPS en el sitio.
    SECURE_REDIRECT_EXEMPT = [r'^health/$']
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'same-origin'
    SECURE_HSTS_SECONDS = 3600
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'cuenta'

# Credenciales únicamente en variables de entorno, nunca en Git.
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
RESEND_API_KEY = config('RESEND_API_KEY', default='')
GMAIL_CLIENT_ID = config('GMAIL_CLIENT_ID', default='')
GMAIL_CLIENT_SECRET = config('GMAIL_CLIENT_SECRET', default='')
GMAIL_REFRESH_TOKEN = config('GMAIL_REFRESH_TOKEN', default='')
# SMTP on Railway requires Pro or above; HTTPS delivery works without SMTP.
RAILWAY_SMTP_ENABLED = config('RAILWAY_SMTP_ENABLED', default=False, cast=bool)
EMAIL_HOST = config('EMAIL_HOST', default='')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)
EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='')
PASSWORD_RESET_TIMEOUT = 1800  # 30 minutos; se invalida al guardar la nueva contraseña.
PUBLIC_BASE_URL = config('PUBLIC_BASE_URL', default=(f'https://{railway_public_domain}' if railway_public_domain else 'http://127.0.0.1:8000' if DEBUG else ''))
