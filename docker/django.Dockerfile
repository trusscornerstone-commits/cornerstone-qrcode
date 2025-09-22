FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependências de build (para psycopg2, pillow c libs, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# (Opcional) Atualiza pip
RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# (Opcional) Remover toolchain se não precisar mais (cuidado se instalar algo que exige compilação dinâmica depois)
# RUN apt-get purge -y build-essential && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

COPY . .

RUN chmod +x docker/entrypoints/django-entrypoint.sh \
    && sed -i 's/\r$//' docker/entrypoints/django-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/docker/entrypoints/django-entrypoint.sh"]