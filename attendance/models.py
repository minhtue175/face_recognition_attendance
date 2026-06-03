


from django.db import models
from accounts.models import Students
from classes.models import Class

class Cameras(models.Model):
    CameraID = models.AutoField(primary_key=True)
    CameraName = models.CharField(max_length=100)
    CameraURL = models.CharField(max_length=500, null=True, blank=True)
    Location = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.CameraName

class Facelogs(models.Model):
    LogID = models.AutoField(primary_key=True)
    DetectTime = models.DateTimeField()
    Confidence = models.FloatField()
    ImagePath = models.CharField(max_length=255)
    Student = models.ForeignKey(Students, on_delete=models.CASCADE)
    Camera = models.ForeignKey(Cameras, on_delete=models.CASCADE)

class AttendanceHistory(models.Model):
    AttendanceID = models.AutoField(primary_key=True)
    AttendanceDate = models.DateField()
    CheckInTime = models.DateTimeField()
    Status = models.CharField(max_length=20)
    Student = models.ForeignKey(Students, on_delete=models.CASCADE)
    Class = models.ForeignKey(Class, on_delete=models.CASCADE)