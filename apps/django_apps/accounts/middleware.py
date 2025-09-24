from django.conf import settings
from django.urls import resolve
from django.contrib.auth.views import redirect_to_login

EXEMPT_NAMES = {
    "login",
    "logout",
    "health",
}

EXEMPT_PATH_PREFIXES = (
    "/static/",
    "/admin/login/",
)

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Se já autenticado, segue
        if request.user.is_authenticated:
            return self.get_response(request)

        path = request.path

        # Prefixos liberados
        for p in EXEMPT_PATH_PREFIXES:
            if path.startswith(p):
                return self.get_response(request)

        # Nomes de rota liberados
        try:
            match = resolve(path)
            if match.view_name in EXEMPT_NAMES:
                return self.get_response(request)
        except Exception:
            # Se não resolver rota (404, etc.), segue fluxo
            pass

        # Redireciona para login com next
        return redirect_to_login(next=path, login_url=getattr(settings, "LOGIN_URL", "/login/"))