from django.contrib import admin
from .models import Subject, Schedule, ClassSession

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('subject', 'code_class', 'account', 'room', 'time_start', 'time_end')
    list_filter  = ('account',)

@admin.register(ClassSession)
class ClassSessionAdmin(admin.ModelAdmin):
    list_display = ('schedule', 'date', 'room', 'start_time', 'end_time')
    list_filter  = ('date',)