from django.shortcuts import render
from .models import Class, StudentClass

def class_list(request):
    """Trang danh sách lớp (Sẽ đắp UI sau)"""
    return render(request, 'classes/class_list.html')



def import_class(request):
    """Trang import danh sách lớp (Sẽ code tính năng sau)"""
    return render(request, 'classes/import_class.html')

def results(request):
    """Trang xem kết quả (Sẽ code tính năng sau)"""
    return render(request, 'classes/results.html')

def schedule(request):
    """Trang xem lịch trình (Sẽ code tính năng sau)"""
    return render(request, 'classes/schedule.html')