# config/settings/prod.py
#
# Alias estable de los settings de producción.
#
# La configuración real vive en `config/settings/production.py` (referenciada
# por manage.py, Dockerfile.prod y docker-compose.prod.yml). Este módulo la
# reexporta para que `--settings=config.settings.prod` funcione sin duplicar
# ni divergir la configuración (una sola fuente de verdad).
#
# Incluye, vía production.py: DEBUG=False, ALLOWED_HOSTS desde env,
# DATABASE_URL vía dj-database-url, STATIC_ROOT, WhiteNoise en MIDDLEWARE,
# SECRET_KEY desde env (fail-fast) y endurecimiento HTTPS/HSTS.
from .production import *  # noqa: F401,F403
