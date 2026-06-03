"""
from django.db import models
from accounts.models import User
from classes.models import ClassSession

class AttendanceRecord(models.Model):
    STATUS_CHOICES = [
        ('present', 'Có mặt'),
        ('absent',  'Vắng'),
        ('late',    'Đi trễ'),
    ]
    session   = models.ForeignKey(ClassSession, on_delete=models.CASCADE,
                                  related_name='records')
    student   = models.ForeignKey(User, on_delete=models.CASCADE,
                                  limit_choices_to={'role': 'student'})
    status    = models.CharField(max_length=10, choices=STATUS_CHOICES,
                                 default='present')
    checkin_time = models.TimeField(null=True, blank=True)
    note      = models.TextField(blank=True)

    class Meta:
        unique_together = ('session', 'student')  # mỗi SV chỉ 1 record/buổi

    def __str__(self):
        return f"{self.student} - {self.session} - {self.status}"
"""


from django.db import models
from accounts.models import User
from classes.models import ClassSession   # ClassSession vẫn còn → OK

class AttendanceRecord(models.Model):
    STATUS_CHOICES = [
        ('present', 'Có mặt'),
        ('absent',  'Vắng'),
        ('late',    'Đi trễ'),
    ]
    session      = models.ForeignKey(ClassSession, on_delete=models.CASCADE,
                                     related_name='records')
    student      = models.ForeignKey(User, on_delete=models.CASCADE,
                                     limit_choices_to={'role': 'student'})
    status       = models.CharField(max_length=10, choices=STATUS_CHOICES,
                                    default='absent')
    checkin_time = models.TimeField(null=True, blank=True)
    note         = models.TextField(blank=True)

    class Meta:
        unique_together = ('session', 'student')
        db_table = 'Attendance'

    def __str__(self):
        return f"{self.student} - {self.session} - {self.status}"