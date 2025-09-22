import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from django.core.asgi import get_asgi_application
from starlette.middleware.cors import CORSMiddleware

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cornerstone.settings")

django_app = get_asgi_application()

api = FastAPI(
    title="Cornerstone API",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url="/api/redoc",
)

@api.get("/api/ping")
def ping():
    return {"pong": True}

@api.get("/health/")
def health():
    return JSONResponse({"status": "ok"})

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Ajuste em produção
    allow_methods=["*"],
    allow_headers=["*"],
)

# Monta Django no root sem WSGIMiddleware
api.mount("/", django_app)

# Este é o callable usado pelo gunicorn (ASGI)
application = api