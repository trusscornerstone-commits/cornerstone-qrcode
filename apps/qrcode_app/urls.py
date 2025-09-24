from django.urls import path
from . import views

urlpatterns = [
    # Página acessada ao escanear o QR
    path("truss/<int:truss_id>/", views.truss_detail_page, name="truss_detail"),
]