FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Instala dependências do sistema, incluindo pg_isready
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client netcat-openbsd curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Garantir permissão e line endings
RUN chmod +x docker/entrypoints/django-entrypoint.sh \
    && sed -i 's/\r$//' docker/entrypoints/django-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/docker/entrypoints/django-entrypoint.sh"]