from django.urls import path
from . import views

urlpatterns = [


    path('', views.attendance_page, name='attendance'),
    path('video_feed/', views.video_feed, name='video_feed'),
    path('save/', views.save_attendance, name='save_attendance'),
    path('session/<int:session_id>/save/', views.save_attendance, name='save_attendance'),
    path('student/history/', views.student_history, name='student_history'),
    
]