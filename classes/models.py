from django.db import models
from accounts.models import Lecturers, Students

class Class(models.Model):
    ClassID = models.AutoField(primary_key=True)
    ClassCode = models.CharField(max_length=20, unique=True)
    ClassName = models.CharField(max_length=100)
    Lecturer = models.ForeignKey(Lecturers, on_delete=models.CASCADE, null=True, blank=True)
    # Thời gian buổi học
    StartTime = models.TimeField(null=True, blank=True)
    EndTime = models.TimeField(null=True, blank=True)
    # Ngày trong tuần (ví dụ: Monday, Tuesday...)
    DayOfWeek = models.CharField(max_length=20, null=True, blank=True)
    # Khoảng thời gian của lớp
    StartDate = models.DateField(null=True, blank=True)
    EndDate = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.ClassCode

class StudentClass(models.Model):
    Student = models.ForeignKey(Students, on_delete=models.CASCADE)
    Class = models.ForeignKey(Class, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('Student', 'Class')