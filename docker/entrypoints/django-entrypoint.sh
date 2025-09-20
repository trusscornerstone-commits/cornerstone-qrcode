#!/bin/sh
set -euo pipefail

# ------------------------------------------------------------------
# Configurações básicas / variáveis
# ------------------------------------------------------------------
PORT="${PORT:-8000}"                          # Render define PORT (ex: 10000)
DJANGO_DEBUG="${DJANGO_DEBUG:-1}"
RUN_MIGRATIONS="${RUN_MIGRATIONS:-1}"
RUN_COLLECTSTATIC="${RUN_COLLECTSTATIC:-0}"   # Em produção prefira coletar no build
GUNICORN_WORKERS="${GUNICORN_WORKERS:-3}"
GUNICORN_TIMEOUT="${GUNICORN_TIMEOUT:-60}"

echo "===> DJANGO_DEBUG=$DJANGO_DEBUG PORT=$PORT RUN_MIGRATIONS=$RUN_MIGRATIONS RUN_COLLECTSTATIC=$RUN_COLLECTSTATIC"

# ------------------------------------------------------------------
# Função opcional: esperar Postgres se quiser (quando DATABASE_URL for postgres)
# ------------------------------------------------------------------
wait_for_postgres () {
  if command -v pg_isready >/dev/null 2>&1; then
    DB_URL="${DATABASE_URL:-}"
    case "$DB_URL" in
      postgres://*|postgresql://*)
        # Extrai host e porta via Python simples
        read DB_HOST DB_PORT <<EOF
$(python - <<'PY'
import os,re
u=os.environ.get("DATABASE_URL","")
m=re.match(r'^postgres(?:ql)?://[^@]+@([^:/]+)(?::(\d+))?/', u)
if m:
    print(m.group(1), m.group(2) or "5432")
PY
)
        if [ -n "${DB_HOST:-}" ]; then
          echo "Esperando Postgres em ${DB_HOST}:${DB_PORT}..."
          for i in $(seq 1 30); do
            if pg_isready -h "$DB_HOST" -p "$DB_PORT" >/dev/null 2>&1; then
              echo "Postgres está pronto."
              return 0
            fi
            echo "Aguardando DB ($i)..."
            sleep 1
          done
          echo "WARN: timeout ao esperar Postgres (tentando mesmo assim)."
        fi
        ;;
    esac
  fi
}

# ------------------------------------------------------------------
# Passo 1: Esperar DB (opcional)
# ------------------------------------------------------------------
wait_for_postgres

# ------------------------------------------------------------------
# Passo 2: Migrations
# ------------------------------------------------------------------
if [ "$RUN_MIGRATIONS" = "1" ]; then
  echo "===> Aplicando migrations..."
  python manage.py migrate --noinput
else
  echo "===> Ignorando migrations (RUN_MIGRATIONS=0)"
fi

# ------------------------------------------------------------------
# Passo 3: Collectstatic (use preferencialmente no build da imagem)
# ------------------------------------------------------------------
if [ "$RUN_COLLECTSTATIC" = "1" ]; then
  echo "===> Collectstatic..."
  python manage.py collectstatic --noinput
fi

# ------------------------------------------------------------------
# Passo 4: Criar superuser automático (opcional - só em dev)
# (Descomente se quiser)
# ------------------------------------------------------------------
# if [ "${AUTO_SUPERUSER:-0}" = "1" ]; then
#   python - <<'PY'
# from django.contrib.auth import get_user_model
# import os
# User = get_user_model()
# u, created = User.objects.get_or_create(
#     username=os.environ.get("DJANGO_SUPERUSER_USERNAME","admin"),
#     defaults={"email": os.environ.get("DJANGO_SUPERUSER_EMAIL","admin@example.com")}
# )
# if created:
#     u.is_staff = True
#     u.is_superuser = True
#     u.set_password(os.environ.get("DJANGO_SUPERUSER_PASSWORD","ChangeMe123!"))
#     u.save()
#     print("Superusuário criado automaticamente.")
# else:
#     print("Superusuário já existia.")
# PY
# fi

# ------------------------------------------------------------------
# Passo 5: Iniciar servidor
# ------------------------------------------------------------------
if [ "$DJANGO_DEBUG" = "1" ]; then
  echo "===> Modo DEV (runserver) na porta $PORT"
  # Quando em dev local com docker-compose você pode mapear 8000:8000 e ignorar $PORT
  exec python manage.py runserver 0.0.0.0:${PORT}
else
  echo "===> Modo PRODUÇÃO (Gunicorn + UvicornWorker) na porta $PORT"
  # Importante: usar ASGI (inclui FastAPI + Django). Não usar wsgi aqui.
  exec gunicorn cornerstone.asgi:application \
      -k uvicorn.workers.UvicornWorker \
      --bind 0.0.0.0:${PORT} \
      --workers "${GUNICORN_WORKERS}" \
      --timeout "${GUNICORN_TIMEOUT}"
fi