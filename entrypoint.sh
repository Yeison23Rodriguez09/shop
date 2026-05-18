#!/bin/sh

# Detener la ejecución si algún comando falla
set -e

echo "==> Ejecutando Migraciones..."
python manage.py migrate --noinput --settings=config.settings.production

echo "==> Recopilando archivos estáticos..."
python manage.py collectstatic --noinput --settings=config.settings.production

echo "==> Iniciando Servidor Gunicorn..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT