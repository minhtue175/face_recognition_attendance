
from django.db import models



from django.contrib.auth.models import AbstractUser

# 1. Bảng User (Thay thế cho bảng Users trong ERD)
class User(AbstractUser):
    # AbstractUser đã có sẵn các trường: id, username, password, email...
    # Hệ thống tự động băm mật khẩu (PasswordHash), nên ta không cần tự viết lại.
    Role = models.CharField(max_length=20, default='student')

    def __str__(self):
        return self.username

# 2. Bảng Giảng viên
class Lecturers(models.Model):
    LecturerID = models.AutoField(primary_key=True)
    FullName = models.CharField(max_length=100)
    Email = models.CharField(max_length=100)
    # Khóa ngoại trỏ về bảng User ở trên
    User = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.FullName

# 3. Bảng Sinh viên
class Students(models.Model):
    StudentID = models.AutoField(primary_key=True)
    FullName = models.CharField(max_length=100)
    Email = models.CharField(max_length=100, null=True, blank=True)
    Phone = models.CharField(max_length=20, null=True, blank=True)
    SEX = models.CharField(max_length=10, null=True, blank=True)
    StudentCode = models.CharField(max_length=20, unique=True)
    AvatarPath = models.CharField(max_length=255, null=True, blank=True)
    # Khóa ngoại trỏ về bảng User ở trên
    User = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.StudentCode