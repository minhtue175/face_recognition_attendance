from django.db import models
from accounts.models import User


class Subject(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'Subject'

    def __str__(self):
        return self.name


class Schedule(models.Model):
    subject    = models.CharField(max_length=255)
    time_start = models.TimeField()
    time_end   = models.TimeField()
    room       = models.CharField(max_length=50)
    serial     = models.CharField(max_length=20, blank=True)
    total      = models.IntegerField(default=0)
    code_class = models.CharField(max_length=20)
    account    = models.ForeignKey(User, on_delete=models.CASCADE,
                                   related_name='schedules')

    class Meta:
        db_table = 'Schedule'

    def __str__(self):
        return f"{self.subject} - {self.code_class}"


class ClassSession(models.Model):
    schedule   = models.ForeignKey(Schedule, on_delete=models.CASCADE,
                                   related_name='sessions',
                                   null=True, blank=True)
    date       = models.DateField()
    room       = models.CharField(max_length=20)
    start_time = models.TimeField()
    end_time   = models.TimeField()

    class Meta:
        db_table = 'ClassSession'

    def __str__(self):
        return f"{self.schedule} - {self.date}"