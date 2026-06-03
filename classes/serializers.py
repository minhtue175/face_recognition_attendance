from rest_framework import serializers
from .models import Class, Session
from accounts.serializers import UserSerializer

class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ['id', 'session_date', 'session_number', 'is_open']

class ClassSerializer(serializers.ModelSerializer):
    teacher = UserSerializer(read_only=True)
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = Class
        fields = ['id', 'class_code', 'class_name', 'teacher',
                  'schedule', 'student_count', 'created_at']

    def get_student_count(self, obj):
        return obj.enrollments.count()