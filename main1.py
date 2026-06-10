import cv2
import numpy as np
import threading
import queue
import time
import traceback
import torch


from core_ai.face_processor import FaceProcessor
from core_ai.attendance_logic import AttendanceManager
from core_ai.MiniFASNet import MiniFASNetV2
from core_ai.generate_patches import CropImage


class AttendanceSystem:
    # ── Tham số hiệu năng ─────────────────────────────────────
    PROCESS_SCALE = 0.4     # Thu ảnh xuống 40% trước khi detect (MTCNN nhanh ~6x)
    AI_INTERVAL   = 0.25    # Giây giữa 2 lần chạy AI cho cùng 1 track

    def __init__(self):
        # ── 1. Face Recognition Model ─────────────────────────
        # SỬA PATH: Trỏ đúng vào thư mục core_ai/models/
        self.processor = FaceProcessor("core_ai/models/final_face_recognizer.pkl")
        self.manager   = AttendanceManager()

        # KHÔNG MỞ CAMERA Ở ĐÂY (Để luồng views.py của Django tự mở bằng CAP_DSHOW)

        # ── 2. Liveness Model (Scale 2.7 - MiniFASNetV2) ─────
        print("🚀 Đang tải mô hình chống giả mạo Liveness (Scale 2.7)...")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.liveness_model = MiniFASNetV2(conv6_kernel=(5, 5))
        
        # SỬA PATH: Trỏ đúng vào thư mục weight nằm trong core_ai/models/
        checkpoint = torch.load("core_ai/models/MobileFaceNet_MultiFT_final.pth", map_location="cpu")
        self.liveness_model.load_state_dict(
            {k.replace("module.", ""): v for k, v in checkpoint.items()}
        )
        self.liveness_model.eval()
        self.liveness_model.to(self.device)

        self.cropper        = CropImage()
        self.liveness_scale = 2.7
        self.track_states   = {}   # {track_id: state_dict}
        print(f"✅ Liveness sẵn sàng (Scale={self.liveness_scale}, LUÔN BẬT)")

        # ── 3. Threading & Queue (Giữ camera mượt 30 FPS) ──
        self._draw_lock = threading.Lock()
        self._draw_data = []
        self._frame_q   = queue.Queue(maxsize=1)
        self._running   = True
        self._ai_status = "⏳ Đang khởi động..."
        self._ai_tick   = 0

        # Kích hoạt luồng AI chạy ngầm song song với Django
        t = threading.Thread(target=self._ai_worker, daemon=True)
        t.start()

    def _batch_liveness(self, bgr_frame, bboxes):
        """Chạy liveness xử lý Batching gom toàn bộ mặt vào 1 lần gọi GPU duy nhất"""
        results   = [True] * len(bboxes)   
        tensors   = []                      
        valid_idx = []                      

        for i, (x1, y1, w, h) in enumerate(bboxes):
            try:
                crop = self.cropper.crop(
                    bgr_frame, [x1, y1, w, h],
                    scale=self.liveness_scale, out_w=80, out_h=80
                )
                t0 = torch.from_numpy(crop.transpose(2, 0, 1)).float()
                t1 = torch.from_numpy(cv2.flip(crop, 1).transpose(2, 0, 1)).float()
                
                margin = int(min(crop.shape[:2]) * 0.05)
                if margin > 0 and crop.shape[0] > 2*margin and crop.shape[1] > 2*margin:
                    crop_zoom = cv2.resize(
                        crop[margin:-margin, margin:-margin],
                        (crop.shape[1], crop.shape[0])
                    )
                else:
                    crop_zoom = crop
                t2 = torch.from_numpy(crop_zoom.transpose(2, 0, 1)).float()

                tensors.extend([t0, t1, t2])
                valid_idx.append(i)
            except Exception:
                pass

        if not tensors:
            return results

        batch = torch.stack(tensors).to(self.device)   
        with torch.no_grad():
            probs = torch.softmax(self.liveness_model(batch), dim=1)[:, 1].cpu().numpy()   

        threshold = 0.6
        for offset, face_idx in enumerate(valid_idx):
            p          = probs[offset*3 : offset*3 + 3]
            votes_real = int(sum(x > threshold for x in p))
            is_real    = (votes_real >= 2)
            results[face_idx] = is_real

        return results

    def _ai_worker(self):
        """Luồng xử lý AI ngầm có tích hợp Cooldown Liveness"""
        while self._running:
            try:
                bgr_frame = self._frame_q.get(timeout=0.5)
            except queue.Empty:
                continue

            try:
                
                h, w = bgr_frame.shape[:2]
                small = cv2.resize(bgr_frame, None, fx=self.PROCESS_SCALE, fy=self.PROCESS_SCALE)
                rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
                sx, sy = w / small.shape[1], h / small.shape[0]

                faces = self.processor.detect_faces(rgb_small)
                detections = np.array([[f['box'][0]*sx, f['box'][1]*sy, (f['box'][0]+f['box'][2])*sx, (f['box'][1]+f['box'][3])*sy, f['confidence']] for f in faces]) if faces else np.empty((0, 5))
                tracked = self.manager.update_tracker(detections)

                current_time = time.time()
                active_tids = {int(obj[4]) for obj in tracked}
                
                # Dọn dẹp bộ nhớ
                for tid in list(self.track_states.keys()):
                    if tid not in active_tids: self.track_states.pop(tid, None)
                for tid in list(self.manager.active_faces.keys()):
                    if tid not in active_tids: self.manager.active_faces.pop(tid, None)

                # ========================================================
                # THIẾT LẬP COOLDOWN Ở ĐÂY (Đơn vị: Giây)
                LIVENESS_COOLDOWN = 3.0  # <--- BẠN CÓ THỂ THAY ĐỔI SỐ 3 NÀY ĐỂ TEST
                # ========================================================

                pending_tids, pending_crops = [], {}               # Dành cho FaceNet
                pending_liveness_tids, pending_liveness_bboxes = [], []  # Dành cho Liveness
                rgb_full = None

                for obj in tracked:
                    x1, y1, x2, y2, tid = (int(v) for v in obj)
                    
                    # Khởi tạo trạng thái lần đầu
                    if tid not in self.track_states:
                        self.track_states[tid] = {
                            'name': 'Detecting...', 
                            'is_real': True, 
                            'last_ai_time': 0.0,
                            'liveness_checked': False,    # Cờ đánh dấu đã check Liveness
                            'last_liveness_time': 0.0     # Thời gian check Liveness cuối cùng
                        }
                    state = self.track_states[tid]

                    # 1. KIỂM TRA COOLDOWN
                    # Nếu đã check là người thật, đếm ngược cooldown để bắt check lại
                    if state['liveness_checked']:
                        if current_time - state['last_liveness_time'] >= LIVENESS_COOLDOWN:
                            state['liveness_checked'] = False # Xóa cờ, yêu cầu AI quét Liveness lại

                    # 2. XẾP HÀNG XỬ LÝ AI
                    if current_time - state['last_ai_time'] >= self.AI_INTERVAL or state['last_ai_time'] == 0.0:
                        state['last_ai_time'] = current_time
                        if rgb_full is None: rgb_full = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
                        
                        # Đưa vào danh sách Nhận diện danh tính
                        pending_crops[tid] = rgb_full[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]
                        pending_tids.append(tid)

                        # Đưa vào danh sách check Liveness (CHỈ KHI CHƯA CHECK HOẶC VỪA HẾT COOLDOWN)
                        if not state['liveness_checked']:
                            pending_liveness_tids.append(tid)
                            pending_liveness_bboxes.append((x1, y1, x2 - x1, y2 - y1))

                # 3. THỰC THI AI: LIVENESS (Chỉ chạy cho người hết Cooldown)
                liveness_results = self._batch_liveness(bgr_frame, pending_liveness_bboxes) if pending_liveness_bboxes else []
                
                for i, tid in enumerate(pending_liveness_tids):
                    state = self.track_states[tid]
                    
                    state['is_real'] = liveness_results[i]
                    state['liveness_checked'] = True           # Bật cờ đã check
                    state['last_liveness_time'] = current_time # Ghi nhận thời gian để tính Cooldown

                # 4. THỰC THI AI: NHẬN DIỆN DANH TÍNH (Vẫn chạy đều đặn mỗi 0.25s)
                for tid in pending_tids:
                    state = self.track_states[tid]
                    state['name'] = self.processor.get_identity(pending_crops[tid]) if tid in pending_crops else "Unknown"
                    self.manager.active_faces[tid] = state['name']

                # 5. CẬP NHẬT TỌA ĐỘ VẼ LÊN MÀN HÌNH
                new_draw = []
                for obj in tracked:
                    x1, y1, x2, y2, tid = (int(v) for v in obj)
                    state = self.track_states.get(tid)
                    if state:
                        name, is_real = state['name'], state['is_real']
                        if not is_real: text, color = "FAKE", (0, 0, 255)
                        elif name != "Unknown":
                            stt, identity = self.manager.get_attendance_info(name, tid)
                            text, color = f"ID:{stt}. {identity}", (0, 255, 0)
                        else: text, color = "Unknown", (0, 165, 255)
                        new_draw.append((x1, y1, x2, y2, text, color))

                with self._draw_lock:
                    self._draw_data = new_draw
                    
            except Exception:
                pass

    def process_frame_async(self, frame):
        """Hàm API trung gian hứng ảnh từ luồng Web Django ném vào Queue xử lý"""
        try:
            self._frame_q.put_nowait(frame.copy())
        except queue.Full:
            try:
                self._frame_q.get_nowait()
                self._frame_q.put_nowait(frame.copy())
            except queue.Empty:
                pass

        with self._draw_lock:
            return list(self._draw_data)