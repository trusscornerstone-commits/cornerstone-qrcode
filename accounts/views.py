from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.http import url_has_allowed_host_and_scheme
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from .models import Truss
import re

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
def truss_qr_view(request):
    qr_data = request.GET.get("qr", "").strip()
    if not qr_data:
        return render(request, "accounts/truss_detail.html", {"error": "QR inválido"})

    # --- Extração robusta dos dados ---
    # Exemplo esperado: "T20A-1 QTY:3 15-05-08"
    match = re.search(r'([A-Za-z0-9]+)(?:-(\d+))?', qr_data)
    truss_id = match.group(1) if match else "?"
    serial_number = int(match.group(2)) if match and match.group(2) else 1

    qty_match = re.search(r'QTY[:\s]+(\d+)', qr_data, re.IGNORECASE)
    quantidade = int(qty_match.group(1)) if qty_match else 1

    # Span (procura o trecho que parece "15-05-08" ou similar)
    span_match = re.search(r'\b\d{2}-\d{2}-\d{2}\b', qr_data)
    span = span_match.group(0) if span_match else ""

    # --- Criação/recuperação da truss ---
    truss, _ = Truss.objects.get_or_create(
        truss_id=truss_id,
        serial_number=serial_number,
        defaults={
            "span": span,
            "quantidade": quantidade,
        },
    )

    # --- Marcar como produzida ---
    if request.method == "POST":
        truss.marcar_produzida(request.user)
        return redirect(request.path + f"?qr={qr_data}")

    return render(request, "accounts/truss_detail.html", {"truss": truss})

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