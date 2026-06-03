from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from classes.models import ClassSession, Schedule
from .models import AttendanceRecord


@login_required
def attendance_page(request):
    if request.user.role != 'teacher':
        return render(request, '403.html', status=403)

    # Lấy tất cả buổi học của giảng viên qua Schedule
    sessions = ClassSession.objects.filter(
        schedule__account=request.user
    ).select_related('schedule').order_by('-date', 'start_time')

    selected_session = None
    students_data    = []
    total = present = rate = 0

    session_id = request.GET.get('session_id')
    if session_id:
        selected_session = get_object_or_404(
            ClassSession,
            id=session_id,
            schedule__account=request.user
        )

        # Lấy sinh viên đã điểm danh trong buổi này
        records = AttendanceRecord.objects.filter(
            session=selected_session
        ).select_related('student').order_by('student__username')

        for rec in records:
            students_data.append({
                'student':      rec.student,
                'status':       rec.status,
                'checkin_time': rec.checkin_time,
            })

        total   = len(students_data)
        present = sum(1 for s in students_data if s['status'] == 'present')
        rate    = round(present / total * 100, 1) if total > 0 else 0

    return render(request, 'attendance/attendance_page.html', {
        'sessions':         sessions,
        'selected_session': selected_session,
        'students_data':    students_data,
        'total':            total,
        'present':          present,
        'rate':             rate,
    })


@require_POST
@login_required
def save_attendance(request):
    try:
        data       = json.loads(request.body)
        session_id = data.get('session_id')
        records    = data.get('records', [])

        session = get_object_or_404(
            ClassSession,
            id=session_id,
            schedule__account=request.user
        )

        for rec in records:
            AttendanceRecord.objects.update_or_create(
                session=session,
                student_id=rec['student_id'],
                defaults={'status': rec['status']}
            )

        return JsonResponse({'ok': True, 'saved': len(records)})

    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)


@login_required
def student_history(request):
    if request.user.role != 'student':
        return render(request, '403.html', status=403)

    records = AttendanceRecord.objects.filter(
        student=request.user
    ).select_related(
        'session',
        'session__schedule',
    ).order_by('-session__date')

    stats = {
        'total':   records.count(),
        'present': records.filter(status='present').count(),
        'absent':  records.filter(status='absent').count(),
        'late':    records.filter(status='late').count(),
    }

    return render(request, 'attendance/student_history.html', {
        'records': records,
        'stats':   stats,
    })