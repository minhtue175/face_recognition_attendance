# -*- coding: utf-8 -*-
# @Time : 20-6-9 下午3:06
# @Author : zhuying
# @Company : Minivision
# @File : generate_patches.py
# @Software : PyCharm
"""
Create patch from original input image by using bbox coordinate
"""

import cv2
import numpy as np


class CropImage:
    def crop(self, org_img, bbox, scale, out_w, out_h, crop=True):
        if not crop:
            return cv2.resize(org_img, (out_w, out_h))
            
        src_h, src_w, _ = np.shape(org_img)
        x = bbox[0]
        y = bbox[1]
        box_w = bbox[2]
        box_h = bbox[3]
        
        # Tính toán kích thước hộp mới dựa trên tỷ lệ phóng đại (scale)
        new_w = box_w * scale
        new_h = box_h * scale
        
        center_x = x + box_w / 2
        center_y = y + box_h / 2
        
        x1 = int(center_x - new_w / 2)
        y1 = int(center_y - new_h / 2)
        x2 = int(center_x + new_w / 2)
        y2 = int(center_y + new_h / 2)
        
        # Xác định khoảng đệm nếu hộp vượt ra ngoài biên ảnh
        pad_top = max(0, -y1)
        pad_bottom = max(0, y2 - src_h + 1)
        pad_left = max(0, -x1)
        pad_right = max(0, x2 - src_w + 1)
        
        if pad_top > 0 or pad_bottom > 0 or pad_left > 0 or pad_right > 0:
            # Dùng REPLICATE thay vì BLACK BORDER để tránh tạo viền đen (nguyên nhân gây FAKE khi ngồi gần)
            padded_img = cv2.copyMakeBorder(org_img, pad_top, pad_bottom, pad_left, pad_right,
                                            cv2.BORDER_REPLICATE)
            # Tịnh tiến tọa độ cắt theo viền đệm
            x1 += pad_left
            x2 += pad_left
            y1 += pad_top
            y2 += pad_top
            crop_img = padded_img[y1:y2+1, x1:x2+1]
        else:
            crop_img = org_img[y1:y2+1, x1:x2+1]
            
        return cv2.resize(crop_img, (out_w, out_h))
