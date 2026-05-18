# beauty_import os
import dj_database_url
from .base import *

DEBUG = False

# SECRET_KEY: en produccion DEBE venir de env. Si no, fallamos al arrancar.
SECRET_KEY = os.getenv('SECRET_KEY', '')
if not SECRET_KEY or SECRET_KEY.startswith('clave-secreta-desarrollo'):
    raise ValueError(
        "SECRET_KEY debe definirse via variable de entorno en produccion."
    )

# Allowed hosts (Render proporciona el dominio por defecto)
ALLOWED_HOSTS = [h.strip() for h in
                 os.getenv('DJANGO_ALLOWED_HOSTS',
                           'shop-4zw8.onrender.com').split(',')
                 if h.strip()]
if not ALLOWED_HOSTS:
    raise ValueError("DJANGO_ALLOWED_HOSTS no está definido correctamente.")

# CSRF_TRUSTED_ORIGINS: Django 4+/5 lo exige para POSTs cross-origin sobre HTTPS
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if o.strip()
] or [f'https://{h}' for h in ALLOWED_HOSTS
      if h not in ('*', 'localhost', '127.0.0.1')]

# Redirección después del login
LOGIN_REDIRECT_URL = '/'

# ==============================================================================
# CONFIGURACIÓN DE LA BASE DE DATOS (CORREGIDA)
# ==============================================================================
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=600,
        ssl_require=True
    )
}

# Archivos estáticos y media
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# WhiteNoise para servir archivos estáticos en producción
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ==============================================================================
# CONFIGURACIÓN DEL CORREO (SMTP) - Tolerante a fallos si no hay variables aún
# ==============================================================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)

# Cambiado a advertencia en consola para evitar que tire el despliegue de la app
if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
    print("⚠️ ADVERTENCIA: EMAIL_HOST_USER y EMAIL_HOST_PASSWORD no están configurados. El envío de correos fallará.")

# Seguridad
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # JS necesita leer csrftoken para fetch protegido
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'same-origin'

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'True').lower() == 'true'

SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '86400'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CORS
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', 'https://shop-4zw8.onrender.com')
if CORS_ALLOWED_ORIGINS:
    CORS_ALLOWED_ORIGINS = CORS_ALLOWED_ORIGINS.split(',')
else:
    CORS_ALLOWED_ORIGINS = []