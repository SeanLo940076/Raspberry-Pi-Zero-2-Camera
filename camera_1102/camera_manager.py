# camera_manager.py

import logging
from picamera2 import Picamera2, Preview
from libcamera import controls
from INA219 import INA219
import cv2
import time
import os

class CameraManager:
    def __init__(self):
        self.picam2 = None
        self.capture_config = None
        self.ina219 = None  # 初始化屬性

    def initialize_camera(self):
        logging.info("Initializing camera...")
        try:
            self.picam2 = Picamera2()

            # 初始化 INA219 感測器
            try:
                self.ina219 = INA219(addr=0x43)  # 根據你的 I2C 地址創建 INA219 感應器（假設地址為 0x43）
                logging.info("INA219 電池感測器初始化成功。")
            except Exception as e:
                logging.error(f"無法初始化 INA219 電池感測器: {e}")
                self.ina219 = None  # 確保在初始化失敗時不嘗試使用

            # 檢查是否存在足夠的感光元件分辨率模式
            if len(self.picam2.sensor_modes) < 3:
                logging.error("Camera does not have enough sensor modes available")
                return False

            # 設置相機模式
            mode1 = self.picam2.sensor_modes[1]
            mode2 = self.picam2.sensor_modes[2]
            preview_config = self.picam2.create_video_configuration(sensor={'output_size': mode1['size'], 'bit_depth': mode1['bit_depth']})
            self.capture_config = self.picam2.create_still_configuration(sensor={'output_size': mode2['size'], 'bit_depth': mode2['bit_depth']})

            self.picam2.configure(preview_config)
            self.picam2.start_preview(Preview.NULL)
            self.picam2.start()

            # 設置 "連續自動對焦" 模式
            self.picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})

            logging.info("Camera initialized and auto-focus set to Continuous.")

            logging.info("Camera initialized successfully.")

            # 丟棄第一張圖像，讓相機穩定
            logging.info("Capturing and discarding first image for stabilization.")
            _ = self.picam2.switch_mode_and_capture_array(self.capture_config)

            return True
        except Exception as e:
            logging.error(f"Failed to initialize camera: {e}")
            return False

    def capture_high_res_image_to_memory(self):
        """
        捕獲一張高解析圖片，並返回其內存數據
        """
        logging.info("正在捕獲高解析度圖片並存入內存...")
        
        # 捕獲高解析度圖像進內存
        high_res_image = self.picam2.switch_mode_and_capture_array(self.capture_config)
        logging.info("圖片捕獲成功，進行色彩格式轉換")

            # # 開始自動對焦
            # try:
            #     logging.info("觸發自動對焦...")
            #     self.picam2.set_controls({"AfMode": controls.AfModeEnum.Auto})
            #     self.picam2.set_controls({"AfTrigger": controls.AfTriggerEnum.Start})
            #     time.sleep(1.0)  # 合理的自動對焦等待時間（根據相機速度調整）
            #     logging.info("自動對焦完成")
            # except Exception as e:
            #     logging.error(f"自動對焦失敗: {e}")
            
            # # 手動設置曝光時間和增益
            # try:
            #     logging.info("設置手動曝光模式並更新曝光時間和增益...")
            #     self.picam2.set_controls({
            #         "AeEnable": 0,                 # 關閉自動曝光
            #         "ExposureTime": 10000,          # 曝光時間設置為 10 毫秒
            #         "AnalogueGain": 2.0             # 調整增益來補償曝光時間縮短
            #     })
            #     logging.info("曝光時間成功設置：曝10毫秒，增益 2.0")
            # except Exception as e:
            #     logging.error(f"設置曝光時間或者增益時發生錯誤: {e}")

        try:
            ## 自動對焦設置：使用持續自動對焦
            self.picam2.set_controls({
                "AfMode": controls.AfModeEnum.Continuous  # 自動持續對焦
            })
            logging.info("自動連續對焦模式已啟用")
            
            ## 設置自動曝光與自動增益（曝光和增益控制放在一起）
            self.picam2.set_controls({
                "AeEnable": 1,  # 啟用自動曝光和自動增益控制
            })
            logging.info("自動曝光和增益已啟用")

            # 捕捉高解析度圖像進內存
            high_res_image = self.picam2.switch_mode_and_capture_array(self.capture_config)
            logging.info("圖片捕獲成功，進行色彩格式轉換")

            # 圖片預處理 — 確保轉換為 RGB 格式
            if high_res_image.shape[2] == 4:
                high_res_image = cv2.cvtColor(high_res_image, cv2.COLOR_BGRA2RGB)
            elif high_res_image.shape[2] == 3:
                high_res_image = cv2.cvtColor(high_res_image, cv2.COLOR_BGR2RGB)
            
            return high_res_image

        except Exception as e:
            logging.error(f"Failed to capture image with auto mode: {e}")
            return None

    def close_camera(self):
        self.picam2.stop()
        self.picam2.close()