from rest_framework import serializers
from .models import Attendance
from accounts.serializers import UserSerializer

class AttendanceSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)

    class Meta:
        model = Attendance
        fields = ['id', 'student', 'status', 'marked_by', 'marked_at']