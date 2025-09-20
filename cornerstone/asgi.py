import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from django.core.asgi import get_asgi_application
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.wsgi import WSGIMiddleware

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cornerstone.settings")

# Instância Django (WSGI via adaptador)
django_app = get_asgi_application()

# Instância FastAPI (pode adicionar docs, tags etc.)
api = FastAPI(
    title="Cornerstone API",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url="/api/redoc",
)

# Exemplo: rota de ping
@api.get("/api/ping")
def ping():
    return {"pong": True}

# Health check (Render usará /health/)
@api.get("/health/")
def health():
    return JSONResponse({"status": "ok"})

# (Exemplo) Endpoint futuramente para gerar QR Code:
# @api.post("/api/qrcode")
# def create_qrcode(data: QRRequestModel): ...

# Configurar CORS se precisar (ajuste origins depois)
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # em produção, restrinja
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar Django na raiz.
# Tudo que não começa com /api ou /health/ cai no Django (templates, admin, etc.)
api.mount("/", WSGIMiddleware(django_app))

# Objeto final exportado para o servidor ASGI
application = api