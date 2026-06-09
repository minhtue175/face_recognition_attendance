from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Class, StudentClass
from accounts.models import Students, Lecturers
import datetime

def class_list(request):
    """Trang danh sách lớp (Sẽ đắp UI sau)"""
    return render(request, 'classes/class_list.html')



def import_class(request):
    """Trang import danh sách lớp: xử lý form import (excel/manual)"""
    if request.method == 'POST':
        subject = request.POST.get('subject')
        class_code = request.POST.get('class_code')
        room = request.POST.get('room')
        serial = request.POST.get('serial')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        method = request.POST.get('method')
        day_of_week = request.POST.get('day_of_week')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        # tìm lecturer tương ứng với user hiện tại (nếu có)
        lecturer = None
        if request.user.is_authenticated:
            lecturer = Lecturers.objects.filter(User=request.user).first()

        # chuẩn bị defaults
        defaults = {
            'ClassName': subject,
            'Lecturer': lecturer,
        }
        if start_time:
            try:
                defaults['StartTime'] = start_time
            except Exception:
                pass
        if end_time:
            try:
                defaults['EndTime'] = end_time
            except Exception:
                pass
        if day_of_week:
            defaults['DayOfWeek'] = day_of_week
        if start_date:
            try:
                defaults['StartDate'] = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
            except Exception:
                pass
        if end_date:
            try:
                defaults['EndDate'] = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
            except Exception:
                pass

        cls, created = Class.objects.update_or_create(ClassCode=class_code, defaults=defaults)

        # Xử lý phương thức thủ công
        if method == 'manual':
            manual = request.POST.get('manual_input', '').strip()
            created_count = 0
            linked_count = 0
            if manual:
                for line in manual.splitlines():
                    code = line.strip()
                    if not code:
                        continue
                    # Nếu chỉ có StudentCode, tìm hoặc tạo student với FullName = mã
                    student, s_created = Students.objects.get_or_create(
                        StudentCode=code,
                        defaults={'FullName': code}
                    )
                    try:
                        sc, linked = StudentClass.objects.get_or_create(Student=student, Class=cls)
                        if s_created:
                            created_count += 1
                        if linked:
                            linked_count += 1
                    except Exception:
                        pass
            messages.success(request, f'Lớp đã được lưu. Tạo {created_count} sinh viên mới, liên kết {linked_count} sinh viên vào lớp (manual).')
        else:
            # TODO: xử lý file Excel nếu cần (hiện chưa cài thư viện)
            messages.success(request, 'Lớp đã được lưu. (Excel import chưa được xử lý)')

        return redirect('import_class')

    return render(request, 'classes/import_class.html')

def results(request):
    """Trang xem kết quả (Sẽ code tính năng sau)"""
    return render(request, 'classes/results.html')

def schedule(request):
    """Trang xem lịch trình (Sẽ code tính năng sau)"""
    return render(request, 'classes/schedule.html')