# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token


# ─── Login ───────────────────────────────────────────────────
def login_view(request):
    # if request.user.is_authenticated:
    #     return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng')

    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


# ─── Dashboard ───────────────────────────────────────────────
@login_required
def dashboard_view(request):
    user = request.user

    # Đã sửa thành .Role viết hoa theo model
    # Hỗ trợ cả 'teacher' và 'lecturer' cho bạn thoải mái setup trong Admin
    if user.Role in ['teacher', 'lecturer', 'giảng viên']:
        return _teacher_dashboard(request, user)
    elif user.Role == 'student':
        return _student_dashboard(request, user)
    else:
        # Admin hoặc role không xác định → về trang admin
        return redirect('admin:index')


def _teacher_dashboard(request, user):
    """Dashboard riêng cho giảng viên."""
    from classes.models import Class
    from accounts.models import Lecturers

    try:
        # Tìm hồ sơ Giảng viên được nối với tài khoản User đang đăng nhập
        lecturer = Lecturers.objects.filter(User=user).first()

        if lecturer:
            today_sessions = Class.objects.filter(Lecturer=lecturer)
            total_classes = today_sessions.count()
        else:
            today_sessions = []
            total_classes = 0

        stats = {
            'total_classes': total_classes,
            'total_students': 0,   # Sẽ đắp logic sau
            'attendance_rate': 0,  # Sẽ đắp logic sau
            'sessions_today': len(today_sessions) if today_sessions else 0,
        }

    except Exception:
        # Bắt lỗi nếu lỡ quên migrate
        today_sessions = []
        stats = {
            'total_classes': 0, 'total_students': 0, 'attendance_rate': 0, 'sessions_today': 0,
        }

    return render(request, 'accounts/dashboard_teacher.html', {
        'user': user,
        'today_sessions': today_sessions,
        'stats': stats,
    })


def _student_dashboard(request, user):
    """Dashboard riêng cho sinh viên."""
    from attendance.models import AttendanceHistory
    from accounts.models import Students
    from django.db.models import Count, Q

    try:
        # Tìm hồ sơ Sinh viên tương ứng với tài khoản User này
        student_profile = Students.objects.get(User=user)

        # Lấy 5 buổi điểm danh gần nhất (Đã map đúng cột)
        records = AttendanceHistory.objects.filter(
            Student=student_profile
        ).select_related('Class').order_by('-AttendanceDate', '-CheckInTime')[:5]

        # Thống kê số buổi
        stats = AttendanceHistory.objects.filter(Student=student_profile).aggregate(
            total=Count('AttendanceID'),
            present=Count('AttendanceID', filter=Q(Status='present')),
            absent=Count('AttendanceID', filter=Q(Status='absent')),
        )
    except Students.DoesNotExist:
        # Nếu tài khoản này chưa được nối với Sinh viên cụ thể thì trả về 0
        records = []
        stats = {'total': 0, 'present': 0, 'absent': 0}

    return render(request, 'accounts/dashboard_student.html', {
        'user': user,
        'records': records,
        'stats': stats,
    })

# ─── API Login (JWT / Token cho frontend) ────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response(
            {'error': 'Vui lòng nhập tên đăng nhập và mật khẩu'},
            status=400
        )

    user = authenticate(username=username, password=password)

    if user:
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'role': user.Role, # Đã sửa thành Role viết hoa để API không lỗi
            'name': user.get_full_name(),
            'username': user.username,
        })

    return Response(
        {'error': 'Sai tên đăng nhập hoặc mật khẩu'},
        status=400
    )

# ─── Profile & Register ──────────────────────────────────────
@login_required
def profile(request):
    """Trang hồ sơ giảng viên — xem và cập nhật thông tin cá nhân"""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name  = request.POST.get('last_name', '').strip()
        user.email      = request.POST.get('email', '').strip()
        # Nếu model User có thêm field phone:
        if hasattr(user, 'phone'):
            user.phone  = request.POST.get('phone', '').strip()
        user.save()
        messages.success(request, 'Cập nhật hồ sơ thành công!')
        return redirect('profile')

    return render(request, 'accounts/profile.html')

# Registration has been disabled: no public register view provided.