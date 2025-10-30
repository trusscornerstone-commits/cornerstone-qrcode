from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),  # agora aponta corretamente para a pasta accounts/
    #path("qrcode/", include("qrcode_app.urls")),  # prefixo para rotas do app qrcode
]
