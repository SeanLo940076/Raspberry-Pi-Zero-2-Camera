# camera_manager.py

import logging
from picamera2 import Picamera2, Preview
import cv2
import time
import os

class CameraManager:
    def __init__(self):
        self.picam2 = None
        self.capture_config = None

    def initialize_camera(self):
        logging.info("Initializing camera...")
        try:
            self.picam2 = Picamera2()

            # 設置相機模式
            mode1 = self.picam2.sensor_modes[1]
            mode2 = self.picam2.sensor_modes[2]
            preview_config = self.picam2.create_video_configuration(sensor={'output_size': mode1['size'], 'bit_depth': mode1['bit_depth']})
            self.capture_config = self.picam2.create_still_configuration(sensor={'output_size': mode2['size'], 'bit_depth': mode2['bit_depth']})

            self.picam2.configure(preview_config)
            self.picam2.start_preview(Preview.NULL)
            self.picam2.start()

            logging.info("Camera initialized successfully.")

            # 丟棄首張圖片，確保相機正常初始化
            logging.info("Capturing and discarding first image for stabilization.")
            _ = self.picam2.switch_mode_and_capture_array(self.capture_config)

            return True
        except Exception as e:
            logging.error(f"Failed to initialize camera: {e}")
            return False

    def capture_high_res_image(self, save_dir):
        logging.info("Capturing high resolution image...")
        try:
            # 切換到拍攝模式並進行拍照
            high_res_image = self.picam2.switch_mode_and_capture_array(self.capture_config)

            # 生成當前時間作為檔名
            current_time = time.strftime("%Y%m%d_%H%M%S")
            image_path = os.path.join(save_dir, f"{current_time}.jpg")

            # 保存圖像文件
            cv2.imwrite(image_path, high_res_image)
            logging.info(f"Image saved as {image_path}")

            return image_path
        except Exception as e:
            logging.error(f"Failed to capture high-resolution image: {e}")
            return None

    def close_camera(self):
        self.picam2.stop()
        self.picam2.close()