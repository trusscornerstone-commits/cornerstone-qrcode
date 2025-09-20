#!/bin/sh
set -e

PORT="${PORT:-8000}"          # Render injeta PORT (ex: 10000)
GUNICORN_WORKERS="${GUNICORN_WORKERS:-3}"
GUNICORN_TIMEOUT="${GUNICORN_TIMEOUT:-60}"

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

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
    echo "Aplicando migrations..."
    python manage.py migrate --noinput
fi

if [ "${RUN_COLLECTSTATIC:-0}" = "1" ]; then
    echo "Collectstatic..."
    python manage.py collectstatic --noinput
fi

echo "Iniciando Django (PORT=$PORT DEBUG=${DJANGO_DEBUG:-?})..."
if [ "${DJANGO_DEBUG}" = "1" ]; then
    exec python manage.py runserver 0.0.0.0:${PORT}
else
    # PRODUÇÃO via ASGI (Django + FastAPI) usando UvicornWorker
    exec gunicorn cornerstone.asgi:application \
        -k uvicorn.workers.UvicornWorker \
        --bind 0.0.0.0:${PORT} \
        --workers "${GUNICORN_WORKERS}" \
        --timeout "${GUNICORN_TIMEOUT}"
fi