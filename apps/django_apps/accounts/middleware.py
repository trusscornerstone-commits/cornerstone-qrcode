from django.conf import settings
from django.urls import resolve
from django.contrib.auth.views import redirect_to_login

EXEMPT_NAMES = {
    "login",
    "logout",
    "health",
    "truss_detail",
    # adicione nomes liberados se necessário (ex.: "admin:login")
}

EXEMPT_PATH_PREFIXES = (
    "/static/",
    "/admin/login/",
)

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            return self.get_response(request)

        path = request.path

        for p in EXEMPT_PATH_PREFIXES:
            if path.startswith(p):
                return self.get_response(request)

        try:
            match = resolve(path)
            if match.view_name in EXEMPT_NAMES:
                return self.get_response(request)
        except Exception:
            pass

        return redirect_to_login(next=path, login_url=getattr(settings, "LOGIN_URL", "/login/"))