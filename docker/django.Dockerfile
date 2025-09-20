FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ajusta permissões do entrypoint
RUN chmod +x docker/entrypoints/django-entrypoint.sh \
    && sed -i 's/\r$//' docker/entrypoints/django-entrypoint.sh

# (Opcional) Coletar estáticos no build para ManifestStorage:
# ENV DJANGO_DEBUG=0 DJANGO_SETTINGS_MODULE=cornerstone.settings
# RUN python manage.py collectstatic --noinput

EXPOSE 8000

ENTRYPOINT ["/app/docker/entrypoints/django-entrypoint.sh"]