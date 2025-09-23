# ---------- STAGE 1: build ----------
FROM python:3.11-slim AS build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=cornerstone.settings \
    DJANGO_DEBUG=0 \
    PYTHONPATH=/install/lib/python3.11/site-packages

WORKDIR /app

# Dependências para compilar (não vão para a imagem final)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl postgresql-client && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir --prefix=/install -r requirements.txt

COPY . .

# Collectstatic (usa fallback SQLite se não houver DATABASE_URL)
RUN python manage.py collectstatic --noinput

# ---------- STAGE 2: runtime ----------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=cornerstone.settings \
    DJANGO_DEBUG=0

WORKDIR /app

# Só libs necessárias em runtime (libpq para psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copia libs Python instaladas no build
COPY --from=build /install /usr/local

# Copia código fonte (se quiser só fontes limpos, poderia excluir testes, etc.)
COPY . .

# Copia staticfiles gerados
COPY --from=build /app/staticfiles /app/staticfiles

RUN chmod +x docker/entrypoints/django-entrypoint.sh && sed -i 's/\r$//' docker/entrypoints/django-entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/app/docker/entrypoints/django-entrypoint.sh"]