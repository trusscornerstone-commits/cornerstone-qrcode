# ---------- STAGE 1: build (instala deps + coleta estáticos) ----------
FROM python:3.11-slim AS build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# (Opcional) instalar dependências do sistema necessários para compilar libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Copia apenas requirements primeiro (cache mais eficiente)
COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

# Copia código do projeto
COPY . .

# Garante ambiente de produção (ou use DJANGO_DEBUG=0 no Render)
ENV DJANGO_SETTINGS_MODULE=cornerstone.settings \
    DJANGO_DEBUG=0

# Coleta arquivos estáticos (Manifest + compressões)
RUN python manage.py collectstatic --noinput

# ---------- STAGE 2: runtime enxuto ----------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copia libs instaladas do stage build
COPY --from=build /install /usr/local

# Copia código
COPY . .

# Copia staticfiles gerados
COPY --from=build /app/staticfiles /app/staticfiles

# (Opcional) expor commit/versão para debug
ARG GIT_COMMIT=unknown
ENV APP_BUILD_COMMIT=$GIT_COMMIT

# Ajusta entrypoint (converte CRLF)
RUN chmod +x docker/entrypoints/django-entrypoint.sh && sed -i 's/\r$//' docker/entrypoints/django-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/docker/entrypoints/django-entrypoint.sh"]