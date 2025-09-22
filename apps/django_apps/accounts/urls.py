from django.urls import path, include
from . import views
from .views import list_users

urlpatterns = [
    path('', views.login_page, name='login'),
    path('home/', views.home, name='home'),
    path('scan/', views.scan_truss, name='scan_truss'),
    path('truss-detail/', views.truss_detail, name='truss_detail'),
    path('em-construcao/', views.em_construcao, name='em_construcao'),
    path('logout/', views.logout_view, name='logout'),
    path('health/', views.health, name='health'),
    path('list-users/', list_users, name='list_users'),

]