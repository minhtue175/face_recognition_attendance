import datetime
import openpyxl
from django.db.models import Count, Q
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Schedule, ClassSession, Subject
from attendance.models import AttendanceRecord
from accounts.models import User


@login_required
def class_list(request):
    schedules = Schedule.objects.filter(
        account=request.user
    ).order_by('subject')
    return render(request, 'classes/class_list.html', {'schedules': schedules})


@login_required
def import_class(request):
    if request.method != 'POST':
        return render(request, 'classes/import_class.html')

    subject_name = request.POST.get('subject', '').strip()
    class_code   = request.POST.get('class_code', '').strip()
    room         = request.POST.get('room', '').strip()
    serial       = request.POST.get('serial', '').strip()
    start_time   = request.POST.get('start_time')
    end_time     = request.POST.get('end_time')
    session_date = request.POST.get('date') or datetime.date.today()
    method       = request.POST.get('method', 'excel')

    # Tạo hoặc lấy Schedule
    schedule_obj, _ = Schedule.objects.get_or_create(
        code_class=class_code,
        account=request.user,
        defaults={
            'subject':    subject_name,
            'room':       room,
            'serial':     serial,
            'time_start': start_time,
            'time_end':   end_time,
        }
    )

    # Tạo buổi học mới
    session = ClassSession.objects.create(
        schedule=schedule_obj,
        date=session_date,
        room=room,
        start_time=start_time,
        end_time=end_time,
    )

    # Xử lý danh sách sinh viên
    students_to_add = []

    if method == 'excel':
        excel_file = request.FILES.get('excel_file')
        if not excel_file:
            messages.error(request, 'Vui lòng chọn file Excel.')
            return redirect('import_class')

        wb = openpyxl.load_workbook(excel_file, data_only=True)
        ws = wb.active
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row[0]:
                continue
            code = str(row[0]).strip()
            name = str(row[1]).strip() if row[1] else ''
            student, _ = User.objects.get_or_create(
                username=code,
                defaults={'first_name': name, 'role': 'student'}
            )
            students_to_add.append(student)

    elif method == 'manual':
        raw = request.POST.get('manual_input', '')
        for line in raw.strip().splitlines():
            parts = [p.strip() for p in line.split(',')]
            if not parts[0]:
                continue
            code = parts[0]
            name = parts[1] if len(parts) > 1 else ''
            student, _ = User.objects.get_or_create(
                username=code,
                defaults={'first_name': name, 'role': 'student'}
            )
            students_to_add.append(student)

    # Lưu sinh viên vào AttendanceRecord cho buổi học này
    for student in students_to_add:
        AttendanceRecord.objects.get_or_create(
            session=session,
            student=student,
            defaults={'status': 'absent'}
        )

    messages.success(
        request,
        f'Import thành công {len(students_to_add)} sinh viên vào lớp {class_code}.'
    )
    return redirect('class_list')


@login_required
def schedule(request):
    """Lịch dạy — tất cả buổi học của giảng viên"""
    sessions = ClassSession.objects.filter(
        schedule__account=request.user
    ).select_related(
        'schedule'
    ).order_by('date', 'start_time')

    return render(request, 'classes/schedule.html', {'sessions': sessions})


@login_required
def results(request):
    """Kết quả điểm danh — thống kê theo từng lịch học"""
    schedules = Schedule.objects.filter(
        account=request.user
    ).select_related('account')

    group_stats = []
    for s in schedules:
        records = AttendanceRecord.objects.filter(
            session__schedule=s
        )
        total   = records.count()
        present = records.filter(status='present').count()
        absent  = records.filter(status='absent').count()
        late    = records.filter(status='late').count()
        rate    = round(present / total * 100) if total > 0 else 0

        group_stats.append({
            'schedule': s,
            'total':    total,
            'present':  present,
            'absent':   absent,
            'late':     late,
            'rate':     rate,
        })

    return render(request, 'classes/results.html', {'group_stats': group_stats})