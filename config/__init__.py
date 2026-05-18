# config/__init__.py
from __future__ import absolute_import, unicode_literals

# Celery es opcional. Si no esta instalado o falla la importacion
# (por ejemplo, si Redis no esta corriendo), el proyecto Django sigue
# funcionando sin tareas asincronas.
try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except Exception:
    celery_app = None
    __all__ = ()
