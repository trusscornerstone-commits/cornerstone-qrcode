from django.urls import path
from . import views

urlpatterns = [
    path("", views.root_redirect, name="root"),
    path("login/", views.login_page, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("home/", views.home, name="home"),
    path("truss-detail/<int:pk>/", views.truss_detail_view, name="truss_detail"),
    path("scan-truss/", views.scan_truss_view, name="scan_truss"),
    path("em-construcao/", views.em_construcao_view, name="em_construcao"),
    path("users/", views.list_users, name="list_users"),
    path("health/", views.health, name="health"),
]