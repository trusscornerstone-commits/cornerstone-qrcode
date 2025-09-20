#!/bin/sh
set -e

# Defaults
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-cornerstone}"

echo "Esperando Postgres em ${DB_HOST}:${DB_PORT}..."
for i in $(seq 1 40); do
    if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" >/dev/null 2>&1; then
        echo "Postgres está pronto."
        break
    fi
    echo "Aguardando ($i)..."
    sleep 1
done

# Rodar migrations uma vez (opcionalmente controlado por var)
if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
    echo "Aplicando migrations..."
    python manage.py migrate --noinput
fi

# Em DEV (DEBUG=1) não precisa collectstatic a cada start
if [ "${RUN_COLLECTSTATIC:-0}" = "1" ]; then
    echo "Collectstatic..."
    python manage.py collectstatic --noinput
fi

# Health endpoint simples (se quiser usar)
# python manage.py shell -c "from django.urls import get_resolver; print('URLs carregadas:', len(get_resolver().url_patterns))"

echo "Iniciando Django..."
if [ "${DJANGO_DEBUG}" = "1" ]; then
    # Sem autoreload? (para evitar restart loops) -> adicione --noreload se quiser
    exec python manage.py runserver 0.0.0.0:8000
else
    # Produção: usar gunicorn
    exec gunicorn cornerstone.wsgi:application --bind 0.0.0.0:8000 --workers 3 --threads 2 --timeout 60
fi