# beauty_shop/config/celery.py
import os
from celery import Celery

# ========================
# ⚙️ Configuración inicial
# ========================

# Carga la configuración del entorno actual (development, production, etc.)
django_env = os.getenv('DJANGO_ENV', 'development').lower()
if django_env == 'production':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# Crea la instancia principal de Celery
app = Celery('beauty_shop')

# Carga configuración de Django usando el prefijo CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-descubrimiento de tareas definidas en todos los apps instalados
app.autodiscover_tasks()


# ========================
# 🐞 Tarea de prueba (opcional)
# ========================
@app.task(bind=True)
def debug_task(self):
    print(f"[Celery Debug] Request: {self.request!r}")
