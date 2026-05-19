FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DJANGO_ENV=production DJANGO_SETTINGS_MODULE=config.settings.production
WORKDIR /app
COPY requirements/prod.txt requirements/prod.txt
COPY requirements/base.txt requirements/base.txt
RUN pip install --upgrade pip && pip install -r requirements/prod.txt
COPY . .
RUN python manage.py collectstatic --noinput
EXPOSE 8000
CMD python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:\ --workers 2 --timeout 120
