from django.urls import path
from . import views

urlpatterns = [
    path('', views.LandingPage, name='index'),
    path('login/', views.LoginPage, name='login'),
    path('signup/', views.SignupPage, name='signup'), 
    path('dashboard/', views.DashboardPage, name='dashboard'),  
    path('logout/', views.LogoutView, name='logout'),
    path('scan/', views.BananaScan, name='scan'),
    path('schedule/', views.Schedule, name='schedule'),
    path('settings/', views.Settings, name='settings'),
    path('api/events/', views.EventsView.as_view(), name='events'),
    path('api/events/<int:event_id>/', views.EventDetailView.as_view(), name='event_detail'),
    path('api/upcoming-events/', views.UpcomingEventsView.as_view(), name='upcoming_events'),
]

