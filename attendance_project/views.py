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
        # Registration disabled: always handle login on POST
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

    # register handling removed


class DashboardView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('home')
        return render(request, 'dashboard.html')


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('home')
