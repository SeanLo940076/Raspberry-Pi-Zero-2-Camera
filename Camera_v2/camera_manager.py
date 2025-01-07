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

            # 檢查是否存在足夠的感光元件分辨率模式
            if len(self.picam2.sensor_modes) < 3:
                logging.error("Camera does not have enough sensor modes available")
                return False

            # 設置相機模式
            mode1 = self.picam2.sensor_modes[1]     # 低解析度：預覽用
            mode2 = self.picam2.sensor_modes[2]     # 高解析度：拍攝用
            self.preview_config = self.picam2.create_video_configuration(sensor={'output_size': mode1['size'], 'bit_depth': mode1['bit_depth']})
            self.capture_config = self.picam2.create_still_configuration(sensor={'output_size': mode2['size'], 'bit_depth': mode2['bit_depth']})

            self.picam2.configure(self.preview_config)
            self.picam2.start_preview(Preview.NULL)
            self.picam2.start()

            # 試拍一張照片並丟棄，幫助穩定 (Warm Up)
            logging.info("Capturing and discarding first image for stabilization.")
            _ = self.picam2.switch_mode_and_capture_array(self.capture_config)

            self.picam2.switch_mode(self.preview_config)

            logging.info("Camera initialized successfully.")

            return True
        except Exception as e:
            logging.error(f"Failed to initialize camera: {e}")
            return False

    def capture_high_res_image_to_memory(self):
        time.sleep(0.2) # 幫助手穩定，因為按下按鈕的瞬間相機會晃動，但我不確定這有沒有用

        logging.info("開始高分辨率拍攝...")
        high_res_image = None

        try:
            # 切換到高分辨率拍照模式，這一步務必首先完成
            logging.info("切換相機至高解析度拍攝模式...")
            self.picam2.switch_mode(self.capture_config)
        except Exception as e:
            logging.error(f"切換至高解析模式失敗: {str(e)}")
            return None

        try:
            # 第二步：設置自動對焦和自動曝光模式，並留一些時間讓相機調整
            self.picam2.set_controls({
                "AfMode": controls.AfModeEnum.Continuous  # 啟用持續自動對焦
            })
            logging.info("已啟用自動對焦")

            self.picam2.set_controls({
                "AeEnable": 1  # 啟用自動曝光
            })
            logging.info("已啟用自動曝光與增益控制")

            # 顯示黑屏圖像，代表正在準備拍照
            logging.info("顯示黑色畫面...")
            self.display_mgr.disp.ShowImage_CV(self.black_image)  # 顯示黑色畫面
            # 等待相機自動對焦與曝光同時快速閃黑色畫面
            time.sleep(0.6)

        except Exception as e:
            logging.error(f"設置自動對焦和曝光失敗: {str(e)}")
            return None

        try:
            # 第三步: 捕捉高解析度圖像
            logging.info("自動對焦和曝光完成，開始拍照...")
            high_res_image = self.picam2.capture_array()
            logging.info("圖片捕獲成功，進行色彩格式轉換")

        except Exception as e:
            logging.error(f"在拍照時出現錯誤: {str(e)}")
            return None

        try:
            logging.info("切換相機至低解析度預覽模式...")
            self.picam2.switch_mode(self.preview_config)
        except Exception as e:
            logging.error(f"切換至預覽模式失敗: {str(e)}")
            return None

        # 圖片預處理 — 確保轉換為 RGB 格式
        if high_res_image.shape[2] == 4:
            high_res_image = cv2.cvtColor(high_res_image, cv2.COLOR_BGRA2RGB)
        elif high_res_image.shape[2] == 3:
            high_res_image = cv2.cvtColor(high_res_image, cv2.COLOR_BGR2RGB)
        
        return high_res_image

    def close_camera(self):
        self.picam2.stop()
        self.picam2.close()