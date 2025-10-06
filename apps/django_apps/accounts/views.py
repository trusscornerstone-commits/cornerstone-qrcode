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
    return HttpResponse("ok", content_type="text/plain")

def root_redirect(request):
    return redirect("home" if request.user.is_authenticated else "login")

TRUSS_CODE_RE = re.compile(r"^T(\d{3,})$")

def truss_generic_view(request):
    qr_raw = (request.GET.get("qr") or "").strip()
    context = {
        "qr_raw": qr_raw,
        "is_url": qr_raw.startswith(("http://", "https://")),
    }
    return render(request, "accounts/truss_generic.html", context)

def truss_base_placeholder(request):
    return HttpResponse(status=204)