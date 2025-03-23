from django.urls import path
from . import views

urlpatterns = [
    path('', views.LandingPage, name='index'),
    path('login/', views.LoginPage, name='login'),
    path('signup/', views.SignupPage, name='signup'), 
    path('dashboard/', views.DashboardPage, name='dashboard'),  
    path('logout/', views.LogoutView, name='logout'),
    path('scan/', views.BananaScan, name='scan'),
]

