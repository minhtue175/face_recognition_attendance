
from django.contrib import admin
from .models import Cameras, Facelogs, AttendanceHistory

admin.site.register(Cameras)
admin.site.register(Facelogs)
admin.site.register(AttendanceHistory)