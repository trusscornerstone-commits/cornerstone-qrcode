from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_page, name='login'),
    path('home/', views.home, name='home'),
    path('truss-detail/', views.truss_detail, name='truss_detail'),
    path('em-construcao/', views.em_construcao, name='em_construcao'),

]