from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme

# LOGIN VIEW
def login_page(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect("home")
        else:
            messages.error(request, "Email ou senha inválidos")
    return render(request, "accounts/login_page.html")

# VIEWS PROTEGIDAS
@login_required(login_url='login')
def home(request):
    return render(request, "accounts/home.html")

@login_required(login_url='login')
def truss_detail(request):
    return render(request, "accounts/truss-detail.html")

@login_required(login_url='login')
def em_construcao(request):
    return render(request, 'accounts/em_construcao.html')

def logout_view(request):
    logout(request)
    return redirect('login')