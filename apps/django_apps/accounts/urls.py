from django.urls import path
from . import views

urlpatterns = [
    path("", views.root_redirect, name="root"),

    # Auth
    path("login/", views.login_page, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # QR genérico (MVP)
    path("truss/generic/", views.truss_generic_view, name="truss_generic"),

    # Protegidas
    path("home/", views.home, name="home"),
    path("truss/<int:pk>/", views.truss_detail_view, name="truss_detail"),
    path("scan-truss/", views.scan_truss_view, name="scan_truss"),
    path("em-construcao/", views.em_construcao_view, name="em_construcao"),

    # Staff JSON
    path("users/", views.list_users, name="list_users"),

    # Health
    path("health/", views.health, name="health"),

    # Prefixo base (se ainda necessário para o front)
    path("truss/base/", views.truss_base_placeholder, name="truss_base"),
]