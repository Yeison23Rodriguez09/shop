# beauty_shop\config\settings\base.py
import os
import dj_database_url
from pathlib import Path

# Base directory del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ========================
# 🌱 Cargar variables de entorno desde .env (si existe)
# ========================
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')
except ImportError:
    # python-dotenv no instalado; las variables se leerán del entorno del sistema
    pass

# ========================
# 🔐 Configuración general
# ========================
SECRET_KEY = os.getenv('SECRET_KEY', 'clave-secreta-desarrollo-NO-USAR-EN-PROD')
DEBUG = False
ALLOWED_HOSTS = []

# ========================
# 🧩 Aplicaciones instaladas
# ========================
INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',

    # Terceros
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'django_celery_results',

    # Locales
    'apps.core',
    'apps.users.apps.UsersConfig',
    'apps.catalog',
    'apps.cart.apps.CartConfig',
    'apps.orders',
    'apps.payments',
    # Apps retiradas del alcance: blog, credits y services (servicios unificados
    # en apps.catalog vía Product.item_type='service'). El importador alternativo
    # (apps.importer) se eliminó por estar vacío; el catálogo se sincroniza con
    # los comandos import_catalog / sync_content / sync_inventory_from_excel.
]

# ========================
# 🧠 Middleware
# ========================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',  # ← debe ir antes de Auth
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ========================
# 📦 Configuración básica
# ========================
ROOT_URLCONF = 'config.urls'            # <-- Aquí estaba la variable faltante
WSGI_APPLICATION = 'config.wsgi.application'
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True
SITE_ID = 1
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ========================
# 🗂️ Templates
# ========================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.media',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.common.context_processors.categories_processor',
                'apps.common.context_processors.service_categories_processor',
                'apps.common.context_processors.cart_session_id',
                'apps.common.context_processors.cart_summary',
                'apps.common.context_processors.shop_info',
            ],
        },
    },
]

# ========================
# 🔐 Password validators
# ========================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ========================
# 📁 Archivos estáticos y media
# ========================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# 📂 Subcarpetas importantes
PRODUCT_EXPORT_PATH = MEDIA_ROOT / 'exports'
PRODUCT_EXPORT_PATH.mkdir(parents=True, exist_ok=True)
PRODUCT_IMAGE_FOLDER = MEDIA_ROOT / 'img'
PRODUCT_IMAGE_FOLDER.mkdir(parents=True, exist_ok=True)

# ========================
# 📧 Email base (sobrescribir en entorno via .env)
# ========================
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@nexoyrsecure.com')
SERVER_EMAIL = os.getenv('SERVER_EMAIL', DEFAULT_FROM_EMAIL)
# Bandeja comercial donde llegan los mensajes del formulario de contacto /
# solicitudes de cotización (canal principal de conversión).
CONTACT_EMAIL = os.getenv('SHOP_CONTACT_EMAIL', DEFAULT_FROM_EMAIL)

# ========================
# 🌐 REST Framework
# ========================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
}

# ========================
# 🗄️ Configuración de Base de Datos
# ========================
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL', 'sqlite:///db.sqlite3'),
        conn_max_age=600
    )
}

# 🛒 Identificador para el carrito de compras en la sesión
CART_SESSION_ID = 'cart'

# Configuración base de allauth (se sobreescribe en development.py)
# allauth 65+ usa ACCOUNT_LOGIN_METHODS (no ACCOUNT_AUTHENTICATION_METHOD)
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_LOGIN_BY_CODE_ENABLED = False
ACCOUNT_EMAIL_VERIFICATION = 'none'   # cambiar a 'mandatory' en producción si quieres verificación por correo
ACCOUNT_RATE_LIMITS = {}              # desactivar rate limiting en desarrollo

# ========================
# 🔑 Autenticación
# ========================
AUTH_USER_MODEL = 'users.CustomUser'
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = '/accounts/login/'

# ========================
# 🗂️ Sesiones — DB-backed para carrito persistente
# ========================
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30  # 30 días
SESSION_SAVE_EVERY_REQUEST = False

# ========================
# 💳 Pasarelas de pago — Colombia
# ========================

# — Wompi (Bancolombia) —
WOMPI_PUBLIC_KEY = os.getenv('WOMPI_PUBLIC_KEY', '')
WOMPI_PRIVATE_KEY = os.getenv('WOMPI_PRIVATE_KEY', '')
WOMPI_INTEGRITY_KEY = os.getenv('WOMPI_INTEGRITY_KEY', '')
WOMPI_EVENTS_KEY = os.getenv('WOMPI_EVENTS_KEY', '')
WOMPI_BASE_URL = 'https://api.wompi.co/v1'
WOMPI_CHECKOUT_URL = 'https://checkout.wompi.co/p/'

# — PayU —
PAYU_API_KEY = os.getenv('PAYU_API_KEY', '')
PAYU_API_LOGIN = os.getenv('PAYU_API_LOGIN', '')
PAYU_MERCHANT_ID = os.getenv('PAYU_MERCHANT_ID', '')
PAYU_ACCOUNT_ID = os.getenv('PAYU_ACCOUNT_ID', '')
PAYU_TEST_MODE = os.getenv('PAYU_TEST_MODE', 'True') == 'True'

# — MercadoPago —
MP_ACCESS_TOKEN = os.getenv('MP_ACCESS_TOKEN', '')
MP_PUBLIC_KEY = os.getenv('MP_PUBLIC_KEY', '')

# ========================
# 🛒 Carrito
# ========================
CART_SESSION_ID = 'cart'

# ========================
# 📧 Correos transaccionales de órdenes
# ========================
ORDER_FROM_EMAIL = os.getenv('ORDER_FROM_EMAIL', DEFAULT_FROM_EMAIL)
