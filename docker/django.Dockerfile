# ---------- STAGE 1: build ----------
FROM python:3.11-slim AS build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=cornerstone.settings \
    DJANGO_DEBUG=0 \
    PYTHONPATH=/install/lib/python3.11/site-packages

WORKDIR /app

# Só o que é necessário para compilar dependências Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir --prefix=/install -r requirements.txt

# Copia o código para coletar estáticos
COPY . .

# Collectstatic não precisa de DB; com DJANGO_SETTINGS_MODULE já definido
RUN python manage.py collectstatic --noinput

# ---------- STAGE 2: runtime ----------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=cornerstone.settings \
    DJANGO_DEBUG=0

WORKDIR /app

# Bibliotecas de runtime:
# - libpq5: lib runtime do PostgreSQL (em vez de libpq-dev)
# - postgresql-client: para pg_isready no entrypoint
# - curl: para healthcheck do docker-compose
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 postgresql-client curl \
 && rm -rf /var/lib/apt/lists/*

# Copia libs Python instaladas no build para o local padrão
COPY --from=build /install /usr/local

# Copia fontes
COPY . .

# Copia staticfiles gerados no build
COPY --from=build /app/staticfiles /app/staticfiles

# Normaliza e garante executável (ENTRYPOINT usa sh, mas mantém por segurança)
RUN sed -i 's/\r$//' docker/entrypoints/django-entrypoint.sh \
 && chmod +x docker/entrypoints/django-entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["sh", "/app/docker/entrypoints/django-entrypoint.sh"]