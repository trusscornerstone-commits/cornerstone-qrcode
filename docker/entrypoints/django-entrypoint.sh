#!/bin/sh
set -e

# ------------------------------------------------------------------
# Configurações básicas (valores default caso não venham do ambiente)
# ------------------------------------------------------------------
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

# ------------------------------------------------------------------
# Migrations
# ------------------------------------------------------------------
if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
    echo "Aplicando migrations..."
    python manage.py migrate --noinput
else
    echo "RUN_MIGRATIONS=0 -> pulando migrations."
fi

# ------------------------------------------------------------------
# Collectstatic (normalmente só em build, mas deixo opcional)
# ------------------------------------------------------------------
if [ "${RUN_COLLECTSTATIC:-0}" = "1" ]; then
    echo "Executando collectstatic..."
    python manage.py collectstatic --noinput
fi

# ------------------------------------------------------------------
# Criação / atualização idempotente de superusuário (USANDO VARIÁVEIS)
# Variáveis esperadas (no Render):
#   CREATE_SUPERUSER=1
#   SUPERUSER_USERNAME=admin
#   SUPERUSER_EMAIL=admin@example.com
#   SUPERUSER_PASSWORD=SenhaForte!2025
# Opcional:
#   SUPERUSER_FORCE_RESET=1  (para forçar redefinição de senha)
# Depois de testar login, REMOVER:
#   CREATE_SUPERUSER e SUPERUSER_PASSWORD
# ------------------------------------------------------------------
if [ "${CREATE_SUPERUSER:-0}" = "1" ]; then
  echo "[bootstrap-admin] Verificando superusuário..."
  python - <<'PY'
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.environ.get("DJANGO_SETTINGS_MODULE","cornerstone.settings"))

import django
try:
    django.setup()
except Exception as e:
    raise SystemExit(f"[bootstrap-admin] ERRO em django.setup(): {e}")

from django.contrib.auth import get_user_model
from django.db import transaction

username = (os.environ.get("SUPERUSER_USERNAME") or "admin").strip()
email = (os.environ.get("SUPERUSER_EMAIL") or "admin@example.com").strip()
password = os.environ.get("SUPERUSER_PASSWORD")
force_reset = os.environ.get("SUPERUSER_FORCE_RESET", "0") == "1"

if not username:
    raise SystemExit("[bootstrap-admin] ERRO: SUPERUSER_USERNAME vazio.")

User = get_user_model()

with transaction.atomic():
    user, created = User.objects.get_or_create(
        username=username,
        defaults={"email": email}
    )
    changed = False

    if user.email != email:
        user.email = email
        changed = True

    if created:
        if not password:
            raise SystemExit("[bootstrap-admin] ERRO: SUPERUSER_PASSWORD ausente para criar.")
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()
        print(f"[bootstrap-admin] Superusuário CRIADO: {username}")
    else:
        if force_reset and password:
            user.set_password(password)
            changed = True
            print("[bootstrap-admin] Senha redefinida (FORCE_RESET=1).")
        if (not user.is_staff) or (not user.is_superuser):
            user.is_staff = True
            user.is_superuser = True
            changed = True
            print("[bootstrap-admin] Flags staff/superuser ajustadas.")
        if changed:
            user.save()
            print(f"[bootstrap-admin] Superusuário ATUALIZADO: {username}")
        else:
            print(f"[bootstrap-admin] Superusuário OK: {username}")

print("[bootstrap-admin] IMPORTANTE: Remova CREATE_SUPERUSER e SUPERUSER_PASSWORD após validar login.")
PY
fi

if [ "${CREATE_SUPERUSER:-0}" = "1" ]; then
  echo "[bootstrap-admin] (debug) Variáveis:"
  echo "  SUPERUSER_USERNAME=${SUPERUSER_USERNAME:-<vazio>}"
  echo "  SUPERUSER_EMAIL=${SUPERUSER_EMAIL:-<vazio>}"
  echo "  SUPERUSER_PASSWORD=${SUPERUSER_PASSWORD:+***SET***}"
  echo "  SUPERUSER_FORCE_RESET=${SUPERUSER_FORCE_RESET:-0}"

  python - <<'PY'
import os, sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.environ.get("DJANGO_SETTINGS_MODULE","cornerstone.settings"))
print("[bootstrap-admin] (debug) DJANGO_SETTINGS_MODULE =", os.environ["DJANGO_SETTINGS_MODULE"])

import django
try:
    django.setup()
except Exception as e:
    print("[bootstrap-admin] ERRO setup:", e, file=sys.stderr)
    raise

from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()
print("[bootstrap-admin] (debug) User model =", User)

username = (os.environ.get("SUPERUSER_USERNAME") or "admin").strip()
email = (os.environ.get("SUPERUSER_EMAIL") or "admin@example.com").strip()
password = os.environ.get("SUPERUSER_PASSWORD")
force_reset = os.environ.get("SUPERUSER_FORCE_RESET", "0") == "1"

print(f"[bootstrap-admin] (debug) Attempt username='{username}' email='{email}' force_reset={force_reset}")

if not username:
    raise SystemExit("[bootstrap-admin] ERRO: SUPERUSER_USERNAME vazio.")

with transaction.atomic():
    user, created = User.objects.get_or_create(
        username=username,
        defaults={"email": email}
    )
    print(f"[bootstrap-admin] (debug) user.id={user.id} created={created}")
    changed = False

    if user.email != email:
        user.email = email
        changed = True
        print("[bootstrap-admin] (debug) email atualizado")

    if created:
        if not password:
            raise SystemExit("[bootstrap-admin] ERRO: SUPERUSER_PASSWORD ausente.")
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()
        print(f"[bootstrap-admin] Superusuário CRIADO: {username}")
    else:
        if force_reset and password:
            user.set_password(password)
            changed = True
            print("[bootstrap-admin] (debug) senha redefinida (force_reset)")
        if (not user.is_staff) or (not user.is_superuser):
            user.is_staff = True
            user.is_superuser = True
            changed = True
            print("[bootstrap-admin] (debug) flags ajustadas")
        if changed:
            user.save()
            print(f"[bootstrap-admin] Superusuário ATUALIZADO: {username}")
        else:
            print(f"[bootstrap-admin] Superusuário OK: {username}")

print("[bootstrap-admin] (debug) Lista de usuários:")
for u in User.objects.all():
    print("  ->", u.id, u.username, u.email, "superuser=", u.is_superuser)
print("[bootstrap-admin] FIM bootstrap (remova debug depois).")
PY
fi
# ------------------------------------------------------------------
# Start do servidor
# ------------------------------------------------------------------
echo "Iniciando Django (PORT=$PORT DEBUG=${DJANGO_DEBUG:-?})..."
if [ "${DJANGO_DEBUG}" = "1" ]; then
    exec python manage.py runserver 0.0.0.0:${PORT}
else
    exec gunicorn cornerstone.asgi:application \
        -k uvicorn.workers.UvicornWorker \
        --bind 0.0.0.0:${PORT} \
        --workers "${GUNICORN_WORKERS}" \
        --timeout "${GUNICORN_TIMEOUT}"
fi