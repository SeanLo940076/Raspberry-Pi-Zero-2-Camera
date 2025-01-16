# camera_manager.py

import logging
from picamera2 import Picamera2, Preview
from libcamera import controls
import cv2
import time
import os
import numpy as np

class CameraManager:
    def __init__(self, display_mgr):
        self.picam2 = None
        self.capture_config = None
        self.display_mgr = display_mgr  # 注入 display_mgr
        self.black_image = np.zeros((240, 240, 3), dtype=np.uint8)  # 假設顯示器為 240x240，可調整

    def initialize_camera(self):
        logging.info("Initializing camera...")
        try:
            self.picam2 = Picamera2()

            if len(self.picam2.sensor_modes) < 3:
                logging.error("Camera does not have enough sensor modes available")
                return False

            mode1 = self.picam2.sensor_modes[1]
            mode2 = self.picam2.sensor_modes[2]
            self.preview_config = self.picam2.create_video_configuration(sensor={'output_size': mode1['size'], 'bit_depth': mode1['bit_depth']})
            self.capture_config = self.picam2.create_still_configuration(sensor={'output_size': mode2['size'], 'bit_depth': mode2['bit_depth']})

            self.picam2.configure(self.preview_config)
            self.picam2.start_preview(Preview.NULL)
            self.picam2.start()

            logging.info("Camera initialized successfully.")
            return True
        except Exception as e:
            logging.error(f"Failed to initialize camera: {e}")
            return False

    def capture_high_res_image_to_memory(self):
        time.sleep(0.2)  # 幫助手穩定

        logging.info("開始高分辨率拍攝...")
        try:
            self.picam2.switch_mode(self.capture_config)
            logging.info("切換相機至高解析度拍攝模式...")
        except Exception as e:
            logging.error(f"切換至高解析模式失敗: {str(e)}")
            return None

        try:
            self.picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})
            self.picam2.set_controls({"AeEnable": 1})
            logging.info("已啟用自動對焦與自動曝光")

            self.display_mgr.disp.ShowImage_CV(self.black_image)
            time.sleep(0.65)  # 等待對焦與曝光
        except Exception as e:
            logging.error(f"設置自動對焦和曝光失敗: {str(e)}")
            return None

        try:
            high_res_image = self.picam2.capture_array()
            if high_res_image is None or high_res_image.size == 0:
                logging.error("捕捉的影像為空或無效")
                return None

            logging.info("圖片捕獲成功，進行色彩格式轉換")
            if high_res_image.shape[2] == 4:
                high_res_image = cv2.cvtColor(high_res_image, cv2.COLOR_BGRA2RGB)
            elif high_res_image.shape[2] == 3:
                high_res_image = cv2.cvtColor(high_res_image, cv2.COLOR_BGR2RGB)

            self.picam2.switch_mode(self.preview_config)
            logging.info("切換相機至低解析度預覽模式")

            return high_res_image
        except Exception as e:
            logging.error(f"拍攝圖片時出現錯誤: {str(e)}")
            return None

    def close_camera(self):
        try:
            self.picam2.stop()
            self.picam2.close()
        except Exception as e:
            logging.error(f"關閉相機時出現錯誤: {e}")