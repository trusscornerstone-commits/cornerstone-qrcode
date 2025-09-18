from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout

def login_page(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Email ou senha inválidos")
    return render(request, "accounts/login_page.html")


@login_required(login_url='login')
def home(request):
    return render(request, "accounts/home.html")

@login_required(login_url='login')
def truss_detail(request):
    return render(request, "accounts/truss-detail.html")
