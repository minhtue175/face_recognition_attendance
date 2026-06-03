# classes/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.class_list, name='class_list'),
    path('import/', views.import_class, name='import_class'),
    path('schedule/', views.schedule,     name='schedule'),  
    path('results/',  views.results,      name='results'),  
]