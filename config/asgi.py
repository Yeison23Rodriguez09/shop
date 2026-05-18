# beauty_shop/config/asgi.py
import os
from django.core.asgi import get_asgi_application

# ========================
# 🌐 Configuración del entorno
# ========================
# Permite cambiar dinámicamente entre entornos según la variable DJANGO_ENV
django_env = os.getenv('DJANGO_ENV', 'development').lower()

if django_env == 'production':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# ========================
# 🚀 ASGI Application
# ========================
application = get_asgi_application()
