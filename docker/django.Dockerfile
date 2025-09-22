FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

COPY . .

# IMPORTANTE: garantir que DJANGO_SETTINGS_MODULE esteja correto
ENV DJANGO_SETTINGS_MODULE=cornerstone.settings \
    DJANGO_DEBUG=0

# Coleta de estáticos (gera arquivos manifest+gzip/brotli)
RUN python manage.py collectstatic --noinput

RUN chmod +x docker/entrypoints/django-entrypoint.sh && sed -i 's/\r$//' docker/entrypoints/django-entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/app/docker/entrypoints/django-entrypoint.sh"]