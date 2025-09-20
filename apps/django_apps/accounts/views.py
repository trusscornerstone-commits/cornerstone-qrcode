from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from django.http import JsonResponse, HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse

User = get_user_model()

@staff_member_required
def list_users(request):
    users = list(User.objects.values('username', 'email'))
    return JsonResponse({'users': users})

def login_page(request):
    if request.method == "POST":
        identifier = request.POST.get("username") or request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=identifier, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(next_url, {request.get_host()}):
                return redirect(next_url)
            return redirect("home")
        messages.error(request, "Email/Usuário ou senha inválidos")
    return render(request, "accounts/login_page.html")

@login_required
def home(request):
    return render(request, "accounts/home.html")

@login_required
def truss_detail(request):
    return render(request, "accounts/truss-detail.html")

@login_required
def em_construcao(request):
    return render(request, 'accounts/em_construcao.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def health(request):
    return JsonResponse({"status": "ok"})