from pathlib import Path
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# --------------------------
# Helpers de ambiente
# --------------------------
def env_bool(name, default=False):
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")

def env_list(name, default=None, sep=","):
    raw = os.environ.get(name)
    if not raw:
        return default or []
    return [v.strip() for v in raw.split(sep) if v.strip()]

# --------------------------
# Segurança básica
# --------------------------
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-insecure-change-me")
DEBUG = env_bool("DJANGO_DEBUG", False)

# ALLOWED_HOSTS: se vazio e DEBUG=True, permite localhost; se produção e vazio -> problema
_raw_hosts = os.environ.get("DJANGO_ALLOWED_HOSTS", "")
if _raw_hosts.strip():
    ALLOWED_HOSTS = [h.strip() for h in _raw_hosts.split(",") if h.strip()]
else:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"] if DEBUG else []

# CSRF_TRUSTED_ORIGINS deve ter formato sem barra final
_raw_csrf = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
if _raw_csrf.strip():
    CSRF_TRUSTED_ORIGINS = [o.rstrip("/") for o in _raw_csrf.split(",") if o.strip()]
else:
    CSRF_TRUSTED_ORIGINS = []

# --------------------------
# Apps
# --------------------------
INSTALLED_APPS = [
    # Opcional (útil no dev para não duplicar static handler do runserver):
    # "whitenoise.runserver_nostatic",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.django_apps.accounts",
    "apps.qrcode_app",
]

# --------------------------
# Middleware
# --------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

if os.getenv("ENABLE_LOGIN_REQUIRED_MW", "0") == "1":
    MIDDLEWARE.append("apps.django_apps.accounts.middleware.LoginRequiredMiddleware")

ROOT_URLCONF = "cornerstone.urls"
WSGI_APPLICATION = "cornerstone.wsgi.application"
ASGI_APPLICATION = "cornerstone.asgi.application"

# URLs de auth (use nomes de rotas para evitar hardcode de caminhos)
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "login"

# --------------------------
# Templates
# --------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --------------------------
# Banco de Dados
# --------------------------
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # Postgres (ou outro) configurado por URL
    DATABASES = {
        "default": dj_database_url.config(default=DATABASE_URL, conn_max_age=600)
    }
else:
    # Fallback para build / dev sem Postgres
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "build.sqlite3",
        }
    }

# --------------------------
# Senhas
# --------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --------------------------
# Locale / Time
# --------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"  # ou "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# --------------------------
# Estáticos
# --------------------------
# Opcional (mas comum em projetos)
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # se você usa uma pasta global "templates/"
        "APP_DIRS": True,                  # habilita templates dentro de cada app
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
STATIC_URL = "/static/"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = BASE_DIR / "staticfiles"

if DEBUG:
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
else:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# --------------------------
# Segurança extra / proxy
# --------------------------
# IMPORTANTE: deixe isso sempre ativo para o Django reconhecer HTTPS atrás do túnel/reverse proxy
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# --------------------------
# Auth
# --------------------------
AUTHENTICATION_BACKENDS = [
    "apps.django_apps.accounts.backends.EmailOrUsernameBackend",
    "django.contrib.auth.backends.ModelBackend",
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Sessão
SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "sessionid")  # ex.: "sessionid_v2"
SESSION_COOKIE_AGE = int(os.getenv("SESSION_COOKIE_AGE", 1209600))
SESSION_EXPIRE_AT_BROWSER_CLOSE = os.getenv("SESSION_EXPIRE_AT_BROWSER_CLOSE", "0") == "1"
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "1") == "1"   # só envia por HTTPS
CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "1") == "1"
SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")    # "Lax" ou "Strict"

# --------------------------
# Log rápido do engine (apenas se quiser)
# --------------------------
if env_bool("PRINT_DB_ENGINE", False):
    try:
        print("DB_ENGINE_AT_RUNTIME:", DATABASES["default"]["ENGINE"])
    except Exception:
        pass

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}