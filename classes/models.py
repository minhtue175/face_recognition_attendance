from django.db import models
from accounts.models import Lecturers, Students

class Class(models.Model):
    ClassID = models.AutoField(primary_key=True)
    ClassCode = models.CharField(max_length=20, unique=True)
    ClassName = models.CharField(max_length=100)
    Lecturer = models.ForeignKey(Lecturers, on_delete=models.CASCADE)

    def __str__(self):
        return self.ClassCode

class StudentClass(models.Model):
    Student = models.ForeignKey(Students, on_delete=models.CASCADE)
    Class = models.ForeignKey(Class, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('Student', 'Class')