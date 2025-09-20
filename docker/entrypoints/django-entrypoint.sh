#!/bin/sh
set -e

PORT="${PORT:-8000}"
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

# --- BLOCO NOVO: criação de superusuário idempotente ---
if [ "${CREATE_SUPERUSER:-0}" = "1" ]; then
  echo "Verificando/gerando superusuário..."
  python - <<'PY'
import os
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()
username = os.environ.get("SUPERUSER_USERNAME", "admin")
email = os.environ.get("SUPERUSER_EMAIL", "admin@example.com")
password = os.environ.get("SUPERUSER_PASSWORD", "ChangeMe123!")

u, created = User.objects.get_or_create(username=username, defaults={"email": email})
# Caso o modelo use email como identificador principal, adapte acima.
u.email = email
u.is_staff = True
u.is_superuser = True
u.set_password(password)
u.save()
print("Superusuário", "CRIADO" if created else "ATUALIZADO", f"-> {username} / {email}")
PY
  echo "Superusuário pronto. (REMOVA CREATE_SUPERUSER depois de confirmar login!)"
fi
# --- FIM BLOCO NOVO ---

echo "Iniciando Django (PORT=$PORT)..."
if [ "${DJANGO_DEBUG}" = "1" ]; then
    exec python manage.py runserver 0.0.0.0:${PORT}
else
    exec gunicorn cornerstone.asgi:application \
        -k uvicorn.workers.UvicornWorker \
        --bind 0.0.0.0:${PORT} \
        --workers "${GUNICORN_WORKERS}" \
        --timeout "${GUNICORN_TIMEOUT}"
fi