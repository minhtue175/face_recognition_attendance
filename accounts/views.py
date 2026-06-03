# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from .forms import RegisterForm


# ─── Login ───────────────────────────────────────────────────
def login_view(request):
    #if request.user.is_authenticated:
    #    return redirect('dashboard')

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

    if user.role == 'teacher':
        return _teacher_dashboard(request, user)
    elif user.role == 'student':
        return _student_dashboard(request, user)
    else:
        # Admin hoặc role không xác định → về trang admin
        return redirect('admin:index')


def _teacher_dashboard(request, user):
    """Dashboard riêng cho giảng viên."""
    # Import ở đây để tránh lỗi nếu model chưa migrate
    try:
        from django.utils import timezone
        from classes.models import ClassSession

        today = timezone.localdate()  # dùng localdate thay vì now().date()

        today_sessions = ClassSession.objects.filter(
            teacher=user,
            date=today
        ).select_related('subject').order_by('start_time')

        # Đếm số lớp khác nhau giảng viên đang dạy
        total_classes = ClassSession.objects.filter(
            teacher=user
        ).values('subject').distinct().count()

        stats = {
            'total_classes': total_classes,
            'total_students': 0,   # tạm thời, cập nhật sau khi có model Enrollment
            'attendance_rate': 0,  # tạm thời
            'sessions_today': today_sessions.count(),
        }

    except Exception:
        # Nếu model chưa có hoặc chưa migrate → hiển thị trang trống
        today_sessions = []
        stats = {
            'total_classes': 0,
            'total_students': 0,
            'attendance_rate': 0,
            'sessions_today': 0,
        }

    return render(request, 'accounts/dashboard_teacher.html', {
        'user': user,
        'today_sessions': today_sessions,
        'stats': stats,
    })


def _student_dashboard(request, user):
    from attendance.models import AttendanceRecord
    from django.db.models import Count, Q

    records = AttendanceRecord.objects.filter(
        student=user
    ).select_related(
        'session__class_group__subject'
    ).order_by('-session__date')[:5]   # 5 buổi gần nhất

    stats = AttendanceRecord.objects.filter(student=user).aggregate(
        total=Count('id'),
        present=Count('id', filter=Q(status='present')),
        absent=Count('id', filter=Q(status='absent')),
    )

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
            'role': user.role,
            'name': user.get_full_name(),
            'username': user.username,
        })

    return Response(
        {'error': 'Sai tên đăng nhập hoặc mật khẩu'},
        status=400
    )

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

def register_view(request):

    if request.method == 'POST':

        form = RegisterForm(request.POST)

        if form.is_valid():

            user = form.save(commit=False)

            user.set_password(
                form.cleaned_data['password']
            )

            user.save()

            messages.success(
                request,
                "Đăng ký thành công"
            )

            return redirect('login')

    else:
        form = RegisterForm()

    return render(
        request,
        'accounts/register.html',
        {'form': form}
    )