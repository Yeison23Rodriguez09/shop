FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Aseguramos permisos de ejecución para el script
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

# Usamos ENTRYPOINT en lugar de CMD con cadenas complejas
ENTRYPOINT ["/app/entrypoint.sh"]