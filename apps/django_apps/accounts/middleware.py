from django.conf import settings
from django.contrib.auth.views import redirect_to_login
import re

# Rotas públicas / não autenticadas
EXEMPT_REGEXES = [
    r"^/login/?$",
    r"^/logout/?$",
    r"^/health/?$",
    r"^/static/.*",
    r"^/scan-truss/?$",        # se quiser permitir abrir a câmera sem login (opcional)
    r"^/truss/generic/?$",     # página genérica de resultado
    r"^/$",                    # root redirect (se desejar liberar)
    r"^/admin/login/?$",       # admin login
]

COMPILED = [re.compile(rx) for rx in EXEMPT_REGEXES]

class LoginRequiredMiddleware:
    """
    Redireciona usuários anônimos para LOGIN_URL,
    exceto caminhos explicitamente liberados.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Se usuário já autenticado -> segue
        if request.user.is_authenticated:
            return self.get_response(request)

        # Checa lista de isenções
        for rx in COMPILED:
            if rx.match(path):
                return self.get_response(request)

        # Redireciona para login
        login_url = getattr(settings, "LOGIN_URL", "/login/")
        return redirect_to_login(next=path, login_url=login_url)