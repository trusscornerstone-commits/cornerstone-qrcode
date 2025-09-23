FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=cornerstone.settings \
    DJANGO_DEBUG=0

WORKDIR /app

# Dependências de sistema (ajuste se não usa Postgres ou Pillow)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl libjpeg-dev zlib1g-dev libpng-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código depois (garante cache das dependências)
COPY . .

# Fallback de DB no settings.py deve existir (usar SQLite se DATABASE_URL não setado)
RUN python manage.py collectstatic --noinput

# Ajusta entrypoint
RUN chmod +x docker/entrypoints/django-entrypoint.sh && sed -i 's/\r$//' docker/entrypoints/django-entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/app/docker/entrypoints/django-entrypoint.sh"]