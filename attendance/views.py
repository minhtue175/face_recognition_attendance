import cv2
import json
import numpy as np
from datetime import date
from django.utils import timezone
from django.shortcuts import render, redirect
from django.http import StreamingHttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q

# Import models từ DB của bạn
from classes.models import Class, StudentClass
from attendance.models import AttendanceHistory, Facelogs
from accounts.models import Students, Lecturers

# Import AI từ thư mục core_ai
from core_ai.face_processor import FaceProcessor
from core_ai.attendance_logic import AttendanceManager


# Khởi tạo AI Model ở dạng biến toàn cục
print("Đang nạp mô hình AI...")
try:
    processor = FaceProcessor("core_ai/models/final_face_recognizer.pkl")
    manager = AttendanceManager()
    print("Nạp mô hình thành công!")
except Exception as e:
    print(f"Lỗi nạp mô hình (Kiểm tra lại đường dẫn): {e}")
    processor = None
    manager = None

# ==========================================
# 1. HÀM HIỂN THỊ GIAO DIỆN CHÍNH (ĐIỂM DANH)
# ==========================================
@login_required
def attendance_page(request):
    """Render ra trang điểm danh, lấy dữ liệu lớp học và sinh viên từ DB"""
   
    # Lấy danh sách lớp DO GIẢNG VIÊN NÀY DẠY để hiển thị ra Dropdown
    try:
        lecturer = Lecturers.objects.get(User=request.user)
        sessions = Class.objects.filter(Lecturer=lecturer)
    except Lecturers.DoesNotExist:
        sessions = []
    
    # Lấy ID lớp học đang được chọn trên URL (?session_id=...)
    session_id = request.GET.get('session_id')
    selected_session = None
    students_data = []
    present = 0
    total = 0
    rate = 0

    if session_id:
        try:
            # Lấy thông tin lớp học (kiểm tra thêm điều kiện lớp này phải của GV này)
            selected_session = Class.objects.get(ClassID=session_id, Lecturer=lecturer)
            
            # Lấy danh sách sinh viên thuộc lớp này qua bảng trung gian
            student_classes = StudentClass.objects.filter(Class=selected_session).select_related('Student')
            total = student_classes.count()

            # Lấy trạng thái điểm danh hôm nay của từng sinh viên
            for sc in student_classes:
                student = sc.Student
                history = AttendanceHistory.objects.filter(
                    Student=student,
                    Class=selected_session,
                    AttendanceDate=date.today()
                ).first()
                
                # Nếu chưa điểm danh, mặc định là 'absent'
                status = history.Status if history else 'absent'
                
                if status == 'present':
                    present += 1
                    
                students_data.append({
                    'student': student,
                    'status': status
                })
            
            if total > 0:
                rate = round((present / total) * 100)
                
        except Class.DoesNotExist:
            pass

    context = {
        'sessions': sessions,
        'selected_session': selected_session,
        'students_data': students_data,
        'present': present,
        'total': total,
        'rate': rate,
    }
    
    return render(request, 'attendance/attendance_page.html', context)


# ==========================================
# 2. HÀM XỬ LÝ API LƯU ĐIỂM DANH TỪ WEB
# ==========================================
def save_attendance(request, session_id=None):
    """Hứng dữ liệu JSON từ nút 'Lưu kết quả' và lưu xuống MySQL"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Lấy session_id từ JSON (ưu tiên) hoặc từ URL
            session_id = data.get('session_id') or session_id
            records = data.get('records', [])
            
            if not session_id:
                return JsonResponse({'ok': False, 'error': 'Chưa chọn lớp học (Thiếu session_id)'})
                
            selected_session = Class.objects.get(ClassID=session_id)
            saved_count = 0
            
            for record in records:
                student_id = record.get('student_id')
                status = record.get('status')
                
                student = Students.objects.get(StudentID=student_id)
                
                # update_or_create: Có rồi thì cập nhật, chưa có thì tạo mới
                AttendanceHistory.objects.update_or_create(
                    Student=student,
                    Class=selected_session,
                    AttendanceDate=date.today(),
                    defaults={
                        'Status': status, 
                        'CheckInTime': timezone.now()
                    }
                )
                saved_count += 1
                
            return JsonResponse({'ok': True, 'saved': saved_count})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})
            
    return JsonResponse({'ok': False, 'error': 'Method không hợp lệ'})


# ==========================================
# 3. HÀM XỬ LÝ LUỒNG CAMERA & AI
# ==========================================
def generate_frames():
    """Đọc camera, xử lý nhận diện AI và đẩy stream lên web"""
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) 

    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        names_in_this_frame = set()             
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 1. Phát hiện mặt
        if processor:
            faces = processor.detect_faces(rgb_frame)
            detections = np.array([[f['box'][0], f['box'][1], f['box'][0]+f['box'][2], f['box'][1]+f['box'][3], f['confidence']] for f in faces])
        else:
            detections = []
            
        if len(detections) == 0: 
            detections = np.empty((0, 5))
        
        # 2. Tracking
        if manager:
            tracked_objs = manager.update_tracker(detections)
        else:
            tracked_objs = []
        
        # 3. Xử lý logic từng khuôn mặt
        for obj in tracked_objs:
            x1, y1, x2, y2, track_id = [int(v) for v in obj]
            
            if manager.is_new_id(track_id):
                face_crop = rgb_frame[max(0, y1):y2, max(0, x1):x2]
                if face_crop.size != 0:
                    name = processor.get_identity(face_crop)
                else:
                    name = "Unknown"
            else:
                name = manager.active_faces.get(track_id, "Unknown")
            
            stt, identity = manager.get_attendance_info(name, track_id)
            
            if identity != "Unknown":
                if identity in names_in_this_frame:
                    display_text = f"WARN: Duplicate {identity}"
                    color = (0, 0, 255) 
                else:
                    display_text = f"ID: {stt}. {identity}"
                    color = (0, 255, 0) 
                    names_in_this_frame.add(identity) 
            else:
                display_text = "Unknown"
                color = (0, 165, 255) 
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, display_text, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # 4. Mã hóa ảnh
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

def video_feed(request):
    """API endpoint để web gọi stream"""
    return StreamingHttpResponse(generate_frames(), content_type='multipart/x-mixed-replace; boundary=frame')


# ==========================================
# 4. CÁC HÀM PHỤ (Lịch sử)
# ==========================================

@login_required
def student_history(request):
    """Trang xem lịch sử ĐẦY ĐỦ của sinh viên"""
    if request.user.Role != 'student':
        return redirect('dashboard')

    try:
        student_profile = Students.objects.get(User=request.user)
        # Lấy TOÀN BỘ lịch sử điểm danh thay vì 5 dòng gần nhất
        records = AttendanceHistory.objects.filter(
            Student=student_profile
        ).select_related('Class').order_by('-AttendanceDate', '-CheckInTime')

        # Thống kê tổng quan
        stats = AttendanceHistory.objects.filter(Student=student_profile).aggregate(
            total=Count('AttendanceID'),
            present=Count('AttendanceID', filter=Q(Status='present')),
            absent=Count('AttendanceID', filter=Q(Status='absent')),
        )
    except Students.DoesNotExist:
        records = []
        stats = {'total': 0, 'present': 0, 'absent': 0}

    return render(request, 'attendance/student_history.html', {
        'records': records,
        'stats': stats
    })


@login_required
def teacher_history_view(request):
    """Trang xem lịch sử dành cho Giảng viên"""
    # Chỉ Giảng viên mới được vào
    if request.user.Role not in ['teacher', 'lecturer', 'giảng viên']:
        return redirect('dashboard')

    try:
        # Tìm hồ sơ Giảng viên
        lecturer = Lecturers.objects.get(User=request.user)
        # Lấy tất cả các lớp do Giảng viên này dạy
        classes = Class.objects.filter(Lecturer=lecturer)
        # Lấy toàn bộ lịch sử điểm danh của các lớp đó
        records = AttendanceHistory.objects.filter(
            Class__in=classes
        ).select_related('Student', 'Class').order_by('-AttendanceDate', '-CheckInTime')
    except Lecturers.DoesNotExist:
        records = []

    return render(request, 'attendance/teacher_history.html', {'records': records})