# attendance/admin.py
from django.contrib import admin
from .models import AttendanceRecord

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'session', 'status', 'checkin_time')
    list_filter = ('status', 'session__date')
    search_fields = ('student__username', 'student__first_name')