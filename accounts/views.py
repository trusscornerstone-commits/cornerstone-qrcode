from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.http import url_has_allowed_host_and_scheme
from django.http import JsonResponse, HttpResponse
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

import re
from django.http import JsonResponse

def truss_qr_redirect(request):
    qr_code_raw = request.GET.get("qr", "").strip()
    if not qr_code_raw:
        return JsonResponse({"error": "QR code vazio"}, status=400)

    # Limpeza básica
    qr_code_text = qr_code_raw.replace("\r", " ").replace("\n", " ").strip()

    # Exemplo: "T20A QTY: 3 15-05-08"
    # Vamos capturar cada parte:
    pattern = r"(?P<truss_id>[A-Z]+\d+[A-Z]*)\s+QTY:\s*(?P<qty>\d+)\s+(?P<span>\d{2}-\d{2}-\d{2})"
    match = re.search(pattern, qr_code_text)

    if not match:
        print(f"[ERRO] QR inválido: {qr_code_text}")
        return JsonResponse({"error": "Formato do QR inválido", "raw": qr_code_text}, status=400)

    data = match.groupdict()
    truss_id = data["truss_id"]
    qty = int(data["qty"])
    span = data["span"]

    # Mostra no terminal (ou substitua por gravação em arquivo / banco)
    print("=== QR CODE LIDO ===")
    print(f"Truss ID: {truss_id}")
    print(f"Quantidade: {qty}")
    print(f"Span: {span}")
    print("====================")

    # Exemplo opcional: salvar em arquivo local temporário
    with open("qrcode_data_log.txt", "a", encoding="utf-8") as f:
        f.write(f"{truss_id}, {qty}, {span}\n")

    # Retorna como JSON (útil para testar via navegador)
    return JsonResponse({
        "status": "ok",
        "truss_id": truss_id,
        "qty": qty,
        "span": span,
        "raw": qr_code_text,
    })



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