from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.http import url_has_allowed_host_and_scheme
from django.http import JsonResponse, HttpResponse
import re
from .models import Truss

User = get_user_model()


def login_page(request):
    if request.method == "POST":
        identifier = request.POST.get("username") or request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=identifier, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get("next")
            if next_url and url_has_allowed_host_and_scheme(next_url, {request.get_host()}):
                return redirect(next_url)
            return redirect("home")
        messages.error(request, "Email/Usuário ou senha inválidos")
    return render(request, "accounts/login_page.html")


@login_required
def home(request):
    return render(request, "accounts/home.html")


@login_required
def truss_detail_view(request, pk: int):
    truss = get_object_or_404(Truss, pk=pk)
    return render(request, "accounts/truss_detail.html", {"truss": truss})

def truss_detail(request, truss_id: int):
    # Encaminha para a implementação existente esperando 'pk'
    return truss_detail_view(request, pk=truss_id)


@login_required
def scan_truss_view(request):
    return render(request, "accounts/scan_truss.html")


@login_required
def em_construcao_view(request):
    return render(request, "accounts/em_construcao.html")


@staff_member_required
def list_users(request):
    users = list(User.objects.values("username", "email"))
    return JsonResponse({"users": users})


def logout_view(request):
    logout(request)
    return redirect("login")


def health(request):
    return JsonResponse({"status": "ok"})

from django.shortcuts import redirect

def root_redirect(request):
    if request.user.is_authenticated:
        return redirect("home")
    return redirect("login")

# Regex opcional para futuro (ex.: T###)
TRUSS_CODE_RE = re.compile(r'^T(\d{3,})$')

def truss_generic_view(request):
    """
    MVP: exibe o conteúdo bruto lido do QR em /truss/generic/?qr=...
    Futuro:
      - Se bater padrão interno (ex.: T123) -> redirect('truss_detail', pk=123)
      - Se for URL externa -> botão 'Abrir'
    """
    qr_raw = (request.GET.get("qr") or "").strip()

    # Exemplo futuro (deixe comentado por enquanto):
    # m = TRUSS_CODE_RE.match(qr_raw)
    # if m:
    #     pk = int(m.group(1))
    #     return redirect('truss_detail', pk=pk)

    context = {
        "qr_raw": qr_raw,
        "is_url": qr_raw.startswith("http://") or qr_raw.startswith("https://"),
    }
    return render(request, "accounts/truss_generic.html", context)