"""
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('teacher', 'Giảng viên'),
        ('student', 'Sinh viên'),
        ('admin',   'Quản trị viên'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=15, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    def is_teacher(self):
        return self.role == 'teacher'

    def is_student(self):
        return self.role == 'student'

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"
"""

from django.contrib.auth.models import AbstractUser
from django.db import models

class Infor(models.Model):
    """Thông tin cá nhân — dùng chung cho giảng viên"""
    name     = models.CharField(max_length=255)
    email    = models.EmailField(blank=True)
    phone    = models.CharField(max_length=20, blank=True)
    sex      = models.CharField(max_length=10, blank=True)
    birthday = models.DateField(null=True, blank=True)
    url      = models.URLField(blank=True)   # avatar URL

    class Meta:
        db_table = 'Infor'

    def __str__(self):
        return self.name


"""class User(AbstractUser):
    ROLE_CHOICES = [
        ('teacher', 'Giảng viên'),
        ('student', 'Sinh viên'),
        ('admin',   'Admin'),
    ]
    role    = models.CharField(max_length=10, choices=ROLE_CHOICES, default='teacher')
    infor   = models.OneToOneField(Infor, on_delete=models.SET_NULL,
                                   null=True, blank=True)

    class Meta:
        db_table = 'Account'

    def __str__(self):
        return self.username"""
    
class User(AbstractUser):
    ROLE_CHOICES = [
        ('teacher', 'Giảng viên'),
        ('student', 'Sinh viên'),
        ('admin', 'Admin'),
    ]

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='student'
    )

    infor = models.OneToOneField(
        Infor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'Account'

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = 'admin'
            self.is_staff = True

        super().save(*args, **kwargs)

    def __str__(self):
        return self.username

class Student(models.Model):
    code_student = models.CharField(max_length=50, unique=True)  # mã SV
    name         = models.CharField(max_length=255)
    phone        = models.CharField(max_length=20, blank=True)
    birthday     = models.DateField(null=True, blank=True)
    sex          = models.CharField(max_length=10, blank=True)
    base_class   = models.CharField(max_length=50, blank=True)   # lớp gốc
    status       = models.CharField(max_length=20, default='active')
    url_avatar   = models.URLField(blank=True)
    url_attend   = models.URLField(blank=True)

    class Meta:
        db_table = 'Student'

    def __str__(self):
        return f"{self.code_student} - {self.name}"