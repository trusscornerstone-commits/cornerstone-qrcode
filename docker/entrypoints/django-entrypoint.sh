#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------
# Funções utilitárias
# ---------------------------------------------
bool() {
  # Normaliza uma string para boolean (0/1)
  case "${1:-}" in
    1|true|TRUE|yes|on|On|ON) return 0 ;;
    *) return 1 ;;
  esac
}

log()  { echo "[ENTRYPOINT] $*"; }
err()  { echo "[ENTRYPOINT][ERRO] $*" >&2; }
hr()   { echo "--------------------------------------------------"; }

# ---------------------------------------------
# Variáveis base
# ---------------------------------------------
PORT="${PORT:-8000}"
GUNICORN_WORKERS="${GUNICORN_WORKERS:-3}"
GUNICORN_TIMEOUT="${GUNICORN_TIMEOUT:-60}"
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-cornerstone}"
WAIT_FOR_DB="${WAIT_FOR_DB:-1}"
CREATE_SUPERUSER="${CREATE_SUPERUSER:-0}"
SUPERUSER_USERNAME="${SUPERUSER_USERNAME:-admin}"
SUPERUSER_EMAIL="${SUPERUSER_EMAIL:-admin@example.com}"
SUPERUSER_PASSWORD="${SUPERUSER_PASSWORD:-}"
SUPERUSER_FORCE_RESET="${SUPERUSER_FORCE_RESET:-0}"
RUN_MIGRATIONS="${RUN_MIGRATIONS:-1}"
FORCE_RUNTIME_COLLECTSTATIC="${FORCE_RUNTIME_COLLECTSTATIC:-0}"  # evitar usar em produção
DEBUG_LOG="${DEBUG_LOG:-0}"  # se quiser logs adicionais
APP_BUILD_COMMIT="${APP_BUILD_COMMIT:-desconhecido}"

# ---------------------------------------------
# Graceful shutdown
# ---------------------------------------------
term_handler() {
  log "Recebido sinal de término. Encerrando..."
  # Gunicorn será finalizado pelo próprio PID 1 (este script).
  exit 0
}
trap term_handler TERM INT

hr
log "Iniciando entrypoint"
log "Commit build: ${APP_BUILD_COMMIT}"
log "PORT=${PORT} WORKERS=${GUNICORN_WORKERS} TIMEOUT=${GUNICORN_TIMEOUT}"

# ---------------------------------------------
# Esperar banco (opcional)
# ---------------------------------------------
if bool "$WAIT_FOR_DB"; then
  log "Esperando Postgres em ${DB_HOST}:${DB_PORT}..."
  for i in $(seq 1 40); do
    if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" >/dev/null 2>&1; then
      log "Postgres está pronto."
      break
    fi
    log "Aguardando ($i)..."
    sleep 1
  done
else
  log "WAIT_FOR_DB=0 -> pulando espera por Postgres."
fi

# ---------------------------------------------
# Sanity check: DEBUG e STATICFILES_STORAGE
# ---------------------------------------------
python - <<'PY'
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.environ.get("DJANGO_SETTINGS_MODULE","cornerstone.settings"))
try:
    from django.conf import settings
    import django
    django.setup()
    print(f"[SANITY] DEBUG = {settings.DEBUG}")
    print(f"[SANITY] STATICFILES_STORAGE = {getattr(settings,'STATICFILES_STORAGE', '<none>')}")
    print(f"[SANITY] STATIC_ROOT = {getattr(settings,'STATIC_ROOT','<none>')}")
except Exception as e:
    print("[SANITY][ERRO] Falha ao inicializar Django:", e)
PY
hr

# ---------------------------------------------
# (Evitar) collectstatic em runtime
# ---------------------------------------------
if bool "$FORCE_RUNTIME_COLLECTSTATIC"; then
  log "FORCE_RUNTIME_COLLECTSTATIC=1 -> executando collectstatic (não recomendado em cada start)."
  python manage.py collectstatic --noinput
else
  log "Não executando collectstatic (deve ter sido feito no build)."
fi

# ---------------------------------------------
# Migrations
# ---------------------------------------------
if bool "$RUN_MIGRATIONS"; then
  log "Aplicando migrations..."
  python manage.py migrate --noinput
else
  log "RUN_MIGRATIONS=0 -> pulando migrations."
fi

# ---------------------------------------------
# Superusuário (idempotente)
# ---------------------------------------------
if bool "$CREATE_SUPERUSER"; then
  if [ -z "$SUPERUSER_PASSWORD" ]; then
    err "CREATE_SUPERUSER=1 mas SUPERUSER_PASSWORD não definido."
  else
    log "Verificando/ajustando superusuário '${SUPERUSER_USERNAME}'..."
    python - <<PY
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.environ.get("DJANGO_SETTINGS_MODULE","cornerstone.settings"))
import django
from django.db import transaction
from django.contrib.auth import get_user_model

django.setup()
User = get_user_model()

username = "${SUPERUSER_USERNAME}".strip()
email    = "${SUPERUSER_EMAIL}".strip()
password = "${SUPERUSER_PASSWORD}"
force_reset = "${SUPERUSER_FORCE_RESET}" in ("1","true","yes","on")

if not username:
    raise SystemExit("[bootstrap-admin] SUPERUSER_USERNAME vazio.")

with transaction.atomic():
    user, created = User.objects.get_or_create(username=username, defaults={"email": email})
    changed = False
    if created:
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()
        print(f"[bootstrap-admin] Superusuário CRIADO: {username}")
    else:
        if user.email != email:
            user.email = email
            changed = True
        if force_reset and password:
            user.set_password(password)
            changed = True
            print("[bootstrap-admin] Senha redefinida (FORCE_RESET=1).")
        if (not user.is_staff) or (not user.is_superuser):
            user.is_staff = True
            user.is_superuser = True
            changed = True
        if changed:
            user.save()
            print(f"[bootstrap-admin] Superusuário ATUALIZADO: {username}")
        else:
            print(f"[bootstrap-admin] Superusuário OK: {username}")

print("[bootstrap-admin] (IMPORTANTE) Remova CREATE_SUPERUSER e SUPERUSER_PASSWORD depois de validar.")
PY
  fi
else
  log "CREATE_SUPERUSER=0 -> não criando superusuário."
fi

if bool "$DEBUG_LOG"; then
  hr
  log "Listando usuários (DEBUG_LOG=1)"
  python - <<'PY'
from django.contrib.auth import get_user_model
from django.conf import settings
try:
    qs = get_user_model().objects.all()
    print(f"[DEBUG] Total usuários: {qs.count()}")
    for u in qs[:10]:
        print("  ->", u.id, u.username, u.email, "superuser=", u.is_superuser)
except Exception as e:
    print("[DEBUG] Falha ao listar usuários:", e)
PY
  hr
fi

# ---------------------------------------------
# Decidir modo: runserver (dev) ou gunicorn (prod)
# ---------------------------------------------
DJANGO_DEBUG="${DJANGO_DEBUG:-0}"
if bool "$DJANGO_DEBUG"; then
  log "DJANGO_DEBUG=1 -> usando runserver (desaconselhado em produção)."
  exec python manage.py runserver 0.0.0.0:"${PORT}"
else
  log "Subindo Gunicorn (ASGI / UvicornWorker)..."
  exec gunicorn cornerstone.asgi:application \
      -k uvicorn.workers.UvicornWorker \
      --bind 0.0.0.0:"${PORT}" \
      --workers "${GUNICORN_WORKERS}" \
      --timeout "${GUNICORN_TIMEOUT}" \
      --log-level info
fi