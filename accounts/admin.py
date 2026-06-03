
from django.contrib import admin
from .models import User, Lecturers, Students

admin.site.register(User)
admin.site.register(Lecturers)
admin.site.register(Students)