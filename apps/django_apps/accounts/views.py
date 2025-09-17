from django.shortcuts import render

def login_page(request):
    return render(request, "accounts/login_page.html")

def home(request):
    return render(request, "accounts/home.html")