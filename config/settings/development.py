import os
from .base import *  # noqa: F401, F403

DEBUG = True
ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',  # noqa: F405
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# CORS
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]
INTERNAL_IPS = ['127.0.0.1']

# ========================
# ⚙️ Allauth — Login por email
# ========================
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_LOGIN_BY_CODE_ENABLED = False
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_LOGIN_ON_PASSWORD_RESET = True
SITE_ID = 1

# ========================
# 💳 Pasarelas de pago — sandbox/test
# ========================
PAYU_TEST_MODE = True
MP_SANDBOX = True

# Wompi — keys de prueba
WOMPI_PUBLIC_KEY = os.getenv('WOMPI_PUBLIC_KEY', 'pub_test_xxxxxx')
WOMPI_PRIVATE_KEY = os.getenv('WOMPI_PRIVATE_KEY', 'prv_test_xxxxxx')
WOMPI_INTEGRITY_KEY = os.getenv('WOMPI_INTEGRITY_KEY', '')
WOMPI_EVENTS_KEY = os.getenv('WOMPI_EVENTS_KEY', '')

# PayU — credenciales sandbox públicas
PAYU_API_KEY = os.getenv('PAYU_API_KEY', '4Vj8eK4rloUd272L48hsrarnUA')
PAYU_API_LOGIN = os.getenv('PAYU_API_LOGIN', 'pRRXKOl8ikMmt9u')
PAYU_MERCHANT_ID = os.getenv('PAYU_MERCHANT_ID', '508029')
PAYU_ACCOUNT_ID = os.getenv('PAYU_ACCOUNT_ID', '512321')

# MercadoPago — token de prueba
MP_ACCESS_TOKEN = os.getenv('MP_ACCESS_TOKEN', 'TEST-xxxxxxxxxx')
MP_PUBLIC_KEY = os.getenv('MP_PUBLIC_KEY', 'TEST-xxxxxxxxxx')
