from django.urls import path
from . import views

urlpatterns = [
    # Raiz: redireciona para login (anônimo) ou home (autenticado)
    path("", views.root_redirect, name="root"),

    # Autenticação
    path("login/", views.login_page, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # Página genérica (MVP) que recebe ?qr=<conteudo>
    path("truss/generic/", views.truss_generic_view, name="truss_generic"),
    
    # Páginas protegidas
    path("home/", views.home, name="home"),
    path("truss/<int:pk>/", views.truss_detail_view, name="truss_detail"),
    path("scan-truss/", views.scan_truss_view, name="scan_truss"),
    path("em-construcao/", views.em_construcao_view, name="em_construcao"),


    # Staff/admin JSON
    path("users/", views.list_users, name="list_users"),

    # Healthcheck
    path("health/", views.health, name="health"),
]