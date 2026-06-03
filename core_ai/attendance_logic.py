from core_ai.sort import Sort

class AttendanceManager:
    def __init__(self):
        # max_age=200 để bám đuôi dai hơn như bạn đã test
        self.tracker = Sort(max_age=200, min_hits=5, iou_threshold=0.2)
        self.active_faces = {}        # {track_id: "Name"}
        
        # Lưu mapping vĩnh viễn cho buổi học: {"Tên": Số_thứ_tự}
        # Ví dụ: {"Tue": 1, "Binh": 2}
        self.attendance_book = {}  

    def update_tracker(self, detections):
        return self.tracker.update(detections)

    def is_new_id(self, track_id):
        return track_id not in self.active_faces

    def get_attendance_info(self, name, track_id):
        """
        Hàm này trả về STT và Tên. Nếu là Unknown thì xử lý riêng.
        """
        self.active_faces[track_id] = name
        
        if name == "Unknown":
            return None, "Unknown"
        
        # Nếu tên này đã có trong sổ điểm danh (đã xuất hiện trước đó)
        if name in self.attendance_book:
            stt = self.attendance_book[name]
            return stt, name
        else:
            # Nếu là người có trong DB nhưng lần đầu tiên xuất hiện
            new_stt = len(self.attendance_book) + 1
            self.attendance_book[name] = new_stt
            print(f"📡 [SERVER] Mời bạn số {new_stt} ({name}) vào lớp!")
            return new_stt, name