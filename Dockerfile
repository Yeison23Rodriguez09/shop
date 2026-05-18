FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

EXPOSE 8000

# Forzamos a Django a usar la configuración de producción en cada paso
CMD ["sh", "-c", "python manage.py migrate --noinput --settings=config.settings.production && python manage.py collectstatic --noinput --settings=config.settings.production && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT"]