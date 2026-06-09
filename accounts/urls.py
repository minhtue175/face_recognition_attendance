from django.urls import path
from . import views

urlpatterns = [
    path('login/',     views.login_view,   name='login'),
    path('logout/',    views.logout_view,  name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('api/login/', views.api_login,    name='api_login'),
    path('profile/',   views.profile,     name='profile'), 
    
]