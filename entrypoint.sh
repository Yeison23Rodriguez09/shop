#!/bin/sh
set -e;

echo "==> Ejecutando Migraciones...";
python manage.py migrate --noinput;

echo "==> Recopilando estáticos...";
python manage.py collectstatic --noinput;

echo "==> Iniciando Gunicorn...";
exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT;