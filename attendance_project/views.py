from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import get_user_model
from django.db import IntegrityError


User = get_user_model()


class HomeView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')

        mode = request.GET.get('mode', 'login')
        return render(request, 'home.html', {
            'active_tab': mode,
        })

    def post(self, request):
        action = request.POST.get('action', 'login')
        if action == 'register':
            return self.handle_register(request)
        return self.handle_login(request)

    def handle_login(self, request):
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is None:
            return render(request, 'home.html', {
                'active_tab': 'login',
                'login_error': 'Tên đăng nhập hoặc mật khẩu không đúng.',
                'login_username': username,
            })

        login(request, user)
        return redirect('dashboard')

    def handle_register(self, request):
        full_name = request.POST.get('full_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        role = request.POST.get('role', 'student')
        student_id = request.POST.get('student_id', '').strip() or None
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')

        errors = []
        if not full_name:
            errors.append('Vui lòng nhập họ tên.')
        if not username:
            errors.append('Vui lòng nhập tên đăng nhập.')
        if not email:
            errors.append('Vui lòng nhập email.')
        if not password or not password2:
            errors.append('Vui lòng nhập mật khẩu và xác nhận mật khẩu.')
        if password != password2:
            errors.append('Mật khẩu xác nhận không khớp.')
        if role == 'student' and not student_id:
            errors.append('Vui lòng nhập mã số sinh viên.')

        if errors:
            return render(request, 'home.html', {
                'active_tab': 'register',
                'register_errors': errors,
                'register_data': {
                    'full_name': full_name,
                    'username': username,
                    'email': email,
                    'role': role,
                    'student_id': student_id,
                },
            })

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                full_name=full_name,
                role=role,
                student_id=student_id if role == 'student' else None,
            )
        except IntegrityError:
            errors.append('Tên đăng nhập hoặc email đã tồn tại. Vui lòng thử tên khác.')
            return render(request, 'home.html', {
                'active_tab': 'register',
                'register_errors': errors,
                'register_data': {
                    'full_name': full_name,
                    'username': username,
                    'email': email,
                    'role': role,
                    'student_id': student_id,
                },
            })

        login(request, user)
        return redirect('dashboard')


class DashboardView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('home')
        return render(request, 'dashboard.html')


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('home')
