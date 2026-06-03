# test_template.py
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_project.settings')
django.setup()

from django.template.loader import get_template

templates = [
    'accounts/login.html',
    'accounts/dashboard_teacher.html',
    'accounts/dashboard_student.html',
]

for t in templates:
    try:
        get_template(t)
        print(f'OK  {t}')
    except Exception as e:
        print(f'LOI {t}: {e}')