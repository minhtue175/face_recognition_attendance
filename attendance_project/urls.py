# attendance_project/urls.py  (cập nhật)
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect  

urlpatterns = [
    path('admin/',      admin.site.urls),
    path('accounts/',   include('accounts.urls')),
    path('api/auth/',   include('accounts.urls')),
    path('api/classes/',        include('classes.urls')),
    path('api/attendance/',        include('attendance.urls')),
    #path('api/', include('attendance.urls')),
    path('',            lambda r: redirect('login')),  
]