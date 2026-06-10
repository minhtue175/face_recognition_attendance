import cv2
import json
import numpy as np
import time
from datetime import date
from django.utils import timezone
from django.shortcuts import render, redirect
from django.http import StreamingHttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
import os
from django.conf import settings


from classes.models import Class, StudentClass
from attendance.models import AttendanceHistory, Facelogs
from accounts.models import Students, Lecturers

# TÍCH HỢP HỆ THỐNG AI MỚI (Từ file main1.py chứa luồng ngầm và Liveness)
from main1 import AttendanceSystem

print("Đang nạp hệ thống AI bất đồng bộ (Liveness & Tracking)...")
try:
    ai_handler = AttendanceSystem()
    print("✅ NẠP MÔ HÌNH THÀNH CÔNG!")
except Exception as e:
    print(f"❌ LỖI NẠP MÔ HÌNH RỒI: {e}")
    ai_handler = None



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
                # BẢO MẬT: Bỏ qua nếu là hình giả (FAKE)
                if record.get('liveness') == False:
                    continue 

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



def generate_frames():
    """Đọc camera và dùng luồng ngầm AI để đẩy stream lên web mượt mà (Đã fix lỗi đơ khi đổi lớp)"""
    global ai_handler
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) 

    try:
        fail_count = 0
        while True:
            # BẢO VỆ: Nếu camera chưa mở hoặc liên tục đọc lỗi (do luồng cũ đang chiếm dụng)
            if not cap.isOpened() or fail_count > 5:
                if cap is not None:
                    cap.release()
                time.sleep(0.3)  # Ngủ 0.3 giây đợi luồng cũ nhả hẳn phần cứng ra
                cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Cố gắng kích hoạt lại camera
                fail_count = 0   # Reset lại bộ đếm lỗi
                
            ret, frame = cap.read()
            if not ret or frame is None:
                fail_count += 1
                time.sleep(0.05)
                continue
                
            fail_count = 0  # Đọc ảnh thành công thì reset bộ đếm lỗi về 0

            # 1. Bơm frame vào cho AI chạy ngầm và lấy tọa độ hộp vẽ cũ/mới nhất ra luôn
            if ai_handler is not None:
                draw_data = ai_handler.process_frame_async(frame)
            else:
                draw_data = []

            # 2. Vẽ ô nhận diện lên hình
            for x1, y1, x2, y2, text, color in draw_data:
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, text, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            # 3. Mã hóa ảnh và trả về cho Web
            ret_enc, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if not ret_enc:
                continue

            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            # Cầm nhịp FPS để luồng Web không bị quá tải
            time.sleep(0.03)

    except GeneratorExit:
        # Trình duyệt ngắt kết nối khi chuyển trang hoặc F5
        pass
    except Exception as e:
        print(f"Lỗi Hệ Thống Stream Camera: {e}")
    finally:
        # LUÔN LUÔN GIẢI PHÓNG CAMERA KHI THOÁT LUỒNG
        if cap is not None:
            cap.release()
        print("🛑 [HỆ THỐNG] Đã tự động nhả Camera an toàn!")

def video_feed(request):
    """API endpoint để web gọi stream"""
    return StreamingHttpResponse(generate_frames(), content_type='multipart/x-mixed-replace; boundary=frame')

# TÍCH HỢP RADAR BẮT LIVENESS THẬT/GIẢ
def get_recent_recognitions(request):
    """API trả về danh sách các khuôn mặt vừa được AI nhận diện kèm Thật/Giả"""
    global ai_handler
    faces = []
    try:
        if ai_handler is not None:
            # Quét các mặt đang có trong luồng Tracker của AI
            for tid, state in list(ai_handler.track_states.items()):
                name = state.get('name')
                is_real = state.get('is_real', True)
                
                # Chỉ xuất ra những mã Sinh viên hợp lệ
                if name and name not in (None, 'Unknown', 'Detecting...'):
                    faces.append({'code': name, 'is_real': bool(is_real)})
    except Exception:
        pass
    
    return JsonResponse({'faces': faces})



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

        # Thống kê tổng quan (CÓ TRẠNG THÁI LATE)
        stats = AttendanceHistory.objects.filter(Student=student_profile).aggregate(
            total=Count('AttendanceID'),
            present=Count('AttendanceID', filter=Q(Status='present')),
            absent=Count('AttendanceID', filter=Q(Status='absent')),
            late=Count('AttendanceID', filter=Q(Status='late')),
        )
    except Students.DoesNotExist:
        records = []
        stats = {'total': 0, 'present': 0, 'absent': 0, 'late': 0}

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