import cv2
import numpy as np
import pickle
from mtcnn import MTCNN
from keras_facenet import FaceNet

class FaceProcessor:
    def __init__(self, model_path):
        print("🚀 Đang khởi tạo AI Models...")
        self.detector = MTCNN()
        self.embedder = FaceNet()
        self.clf, self.le = self._load_model(model_path)
        print("✅ Models đã sẵn sàng với bộ lọc Threshold.")

    def _load_model(self, path):
        with open(path, 'rb') as f:
            return pickle.load(f)

    def detect_faces(self, rgb_frame):
        return self.detector.detect_faces(rgb_frame)

    def get_identity(self, face_img):
        try:
            # 1. Tiền xử lý ảnh (Resize và chuẩn hóa đầu vào cho FaceNet)
            face_img = cv2.resize(face_img, (160, 160))
            face_img = np.expand_dims(face_img, axis=0)
            
            # 2. Trích xuất đặc trưng (Embedding 512 chiều)
            embedding = self.embedder.embeddings(face_img)
            
            # 3. Tính toán xác suất cho từng nhãn (Thay vì dự đoán trực tiếp)
            # predict_proba sẽ trả về mảng xác suất, ví dụ: [0.1, 0.9] (10% là A, 90% là B)
            probs = self.clf.predict_proba(embedding)
            max_prob = np.max(probs) # Lấy giá trị xác suất cao nhất
            
            # 4. THIẾT LẬP NGƯỠNG TIN CẬY (THRESHOLD)
            # Bạn có thể điều chỉnh con số 0.7 này (từ 0.0 đến 1.0)
            # Càng cao thì càng khó nhận diện, nhưng càng chính xác.
            threshold = 0.7 
            
            if max_prob < threshold:
                return "Unknown"
            
            # Nếu vượt qua ngưỡng thì mới lấy tên tương ứng
            pred_idx = np.argmax(probs)
            name = self.le.inverse_transform([pred_idx])[0]
            
            # In ra Terminal để bạn theo dõi độ tự tin của AI khi test
            # print(f"🔍 Nhận diện: {name} - Độ tự tin: {max_prob:.2f}")
            
            return name
        except Exception as e:
            # Nếu có lỗi (ví dụ face_img rỗng do cắt trượt), trả về Unknown
            return "Unknown"