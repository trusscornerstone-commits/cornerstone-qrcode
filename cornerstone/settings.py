"""
Django settings for cornerstone project.
"""

from pathlib import Path
import os
import dj_database_url
from django.core.management.utils import get_random_secret_key

# Caminho base
BASE_DIR = Path(__file__).resolve().parent.parent

# ==== Variáveis de ambiente utilitárias ====
def env_bool(name, default=False):
    return os.environ.get(name, str(int(default))) in ("1", "true", "True", "yes", "on")

def env_list(name, default=None, sep=","):
    raw = os.environ.get(name)
    if not raw:
        return default or []
    return [v.strip() for v in raw.split(sep) if v.strip()]

# ==== Configurações básicas ====
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-insecure-" + get_random_secret_key())

DEBUG = env_bool("DJANGO_DEBUG", True)

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", ["localhost", "127.0.0.1"])

# ==== Aplicativos ====
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.django_apps.accounts",
]

# ==== Middleware ====
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # mantém mesmo em dev; ok
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "cornerstone.urls"

# ==== Templates ====
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

WSGI_APPLICATION = "cornerstone.wsgi.application"

# ==== Banco de Dados ====
DATABASES = {
    "default": dj_database_url.config(
        default=os.environ.get(
            "DATABASE_URL",
            "postgres://cornerstone:cornerstone@db:5432/cornerstone"
        ),
        conn_max_age=600,
    )
}

# ==== Validação de Senhas ====
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ==== Internacionalização / Fuso ====
LANGUAGE_CODE = "en-us"
# Ajustar se quiser horário BR:
# TIME_ZONE = "America/Sao_Paulo"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ==== Arquivos Estáticos ====
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
#STATICFILES_DIRS = [BASE_DIR / "static"]  # certifique-se de que esta pasta existe

if DEBUG:
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
else:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ==== Arquivos de mídia (caso venha a usar) ====
# MEDIA_URL = "/media/"
# MEDIA_ROOT = BASE_DIR / "media"

# ==== Segurança / Proxy ====
CSRF_TRUSTED_ORIGINS = env_list(
    "CSRF_TRUSTED_ORIGINS",
    ["https://cornerstone-app.onrender.com"]
)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# ==== Backends de Autenticação ====
AUTHENTICATION_BACKENDS = [
    "apps.django_apps.accounts.backends.EmailOrUsernameBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# ==== Login / Redirects ====
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "login"

# ==== ID padrão ====
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

