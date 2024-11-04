# state_machine.py

import logging
import os
import cv2
from enum import Enum
import time
from threading import Thread
import numpy as np
import INA219
from libcamera import controls
from picamera2 import Picamera2, Preview

class State(Enum):
    PREVIEW = 1
    VIEW_IMAGE = 2
    CAPTURE = 3

class StateMachine:
    def __init__(self, display_mgr, cam_mgr, key_mgr, save_dir):
        self.display_mgr = display_mgr
        self.camera_mgr = cam_mgr
        self.key_mgr = key_mgr
        self.state = State.PREVIEW
        self.save_dir = save_dir
        self.image_paths = self._get_image_paths_sorted()  # 加載現有圖片路徑
        self.image_index = None
        self.thumbnail_cache = {}  # 用於儲存縮略圖的快取
        self.black_image = np.zeros((self.display_mgr.disp.height, self.display_mgr.disp.width, 3), dtype=np.uint8)
        self.preload_latest_image()

        # 新增緩存機制 - 每隔(30秒)更新一次電池電量數據
        self.last_battery_update_time = 0
        self.cached_battery_percentage = None

    def _get_image_paths_sorted(self):
        """從保存路徑中獲取圖像文件並按時間排序"""
        try:
            files = [os.path.join(self.save_dir, f) for f in os.listdir(self.save_dir) if f.endswith(".jpg")]
            files.sort(key=os.path.getctime)
            return files
        except Exception as e:
            logging.error(f"Failed to get image paths: {e}")
            return []

    def preload_latest_image(self):
        """預加載最新的一張圖片"""
        if len(self.image_paths) == 0:
            logging.info("No images available to preload")
            return

        latest_idx = len(self.image_paths) - 1
        if latest_idx not in self.thumbnail_cache:
            image = cv2.imread(self.image_paths[latest_idx])
            if image is None:
                logging.error(f"Failed to load image: {self.image_paths[latest_idx]}")
                return

            thumbnail = self.generate_thumbnail(image)
            self.thumbnail_cache[latest_idx] = thumbnail
        logging.info(f"最新的圖片已經預加載 image_index: {latest_idx}")

    # def generate_thumbnail(self, image, max_width=240, max_height=135, jpeg_quality=80):
    #     # 根據最大寬度和高度來縮放圖像
    #     original_height, original_width = image.shape[:2]
    #     scale = min(max_width / original_width, max_height / original_height)
    #     new_size = (int(original_width * scale), int(original_height * scale))

    #     # 使用 OpenCV 縮放圖像
    #     thumbnail_img = cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)

    #     # 使用 JPEG 壓縮進行縮略圖存儲
    #     result, encoded_img = cv2.imencode(".jpg", thumbnail_img, [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality])
    #     if result:
    #         thumbnail_img = cv2.imdecode(encoded_img, 1)  # 解碼得到縮略圖
    #     else:
    #         logging.error("Error occurred during thumbnail compression")

    #     return thumbnail_img

    def generate_thumbnail(self, image, max_width=240, max_height=135):
        """
        生成縮略圖，將圖像的尺寸調整至最大為 240x135。
        """
        original_height, original_width = image.shape[:2]
        scale = min(max_width / original_width, max_height / original_height)
        new_size = (int(original_width * scale), int(original_height * scale))

        # 建立縮略圖，使用 OpenCV 進行縮放
        thumbnail_img = cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)
        return thumbnail_img

    def preload_images_around(self, image_index):
        """
        預加載當前圖片的前 3 張和後 3 張圖片，生成縮略圖
        並釋放距離當前圖片 50 張以外的遠處圖片。
        """
        # 1. 調整預加載範圍：前 3、後 3 張
        max_cache_range = 3  # 前後加載 3 張圖片
        start_idx = max(0, image_index - max_cache_range)
        end_idx = min(len(self.image_paths), image_index + max_cache_range + 1)

        # 2. 釋放範圍距離超過 50 張的 "遠處的圖片" 來節省內存
        max_distance_for_cache = 50  # 超過 50 張的圖片被認為是遠處的圖片
        for idx in list(self.thumbnail_cache):  # 深度複製鍵值
            if abs(idx - image_index) > max_distance_for_cache:  # 釋放距離超過 50 張的圖片
                del self.thumbnail_cache[idx]

        # 3. 加載當前範圍內的圖片至快取中（前 3、後 3 張）
        for idx in range(start_idx, end_idx):
            if idx not in self.thumbnail_cache:  # 尚未加載的圖片進行快取
                image = cv2.imread(self.image_paths[idx])
                if image is None:
                    logging.error(f"Failed to read image: {self.image_paths[idx]}")
                    continue

                # 生成縮略圖並存入緩存
                thumbnail = self.generate_thumbnail(image)
                self.thumbnail_cache[idx] = thumbnail

    def get_battery_percentage(self, update_interval=30):
        """
        整合時間緩存機制，每隔指定時間 (update_interval 秒) 更新一次電池電量。
        """
        current_time = time.time()

        # 只有當距離上次更新超過指定 interval 時才讀取 INA219 電池數據
        if current_time - self.last_battery_update_time > update_interval:
            if self.camera_mgr.ina219 is None:
                logging.error("無法獲取電池電量 INA219 未初始化。")
                return None

            try:
                bus_voltage = self.camera_mgr.ina219.getBusVoltage_V()  # 取得負載電壓
                battery_percentage = (bus_voltage - 3) / 1.2 * 100  # 假設為 4.2V ~ 3.0V 電池範圍
                battery_percentage = min(max(battery_percentage, 0), 100)  # 限制在 0-100% 之間

                # 更新緩存值和上次更新時間
                self.cached_battery_percentage = battery_percentage
                self.last_battery_update_time = current_time

                return self.cached_battery_percentage
            except Exception as e:
                logging.error(f"無法獲取電池百分比: {e}")
                return None

        # 如果在 update_interval 時間範圍內，使用緩存值
        return self.cached_battery_percentage

    def handle_preview_state(self):
        # 擷取原始影像 (預覽模式的影像為BGRA格式)
        raw_image = self.camera_mgr.picam2.capture_array()

        # 獲取當前電池電量百分比
        battery_percentage = self.get_battery_percentage()

        # 獲取當前的日期和時間
        current_time = time.strftime("%H:%M:%S")  # Example format: 18:57:05
        current_date = time.strftime("%Y/%m/%d")  # Example format: 2024/11/03

        # 顯示即時影像，狀態為 "Capture"，顯示時間、日期和電池電量
        self.display_mgr.display_image_with_state(raw_image, "Capture", date_text=current_date, time_text=current_time, battery_percentage=battery_percentage)

        # 處理按鍵輸入
        if self.key_mgr.check_key_pressed(self.display_mgr.disp.GPIO_KEY1_PIN):  # 拍照按鍵被按下
            logging.info("KEY1 按下，正在觸發一次自動對焦和拍照...")

            # ## 自動對焦
            # self.camera_mgr.picam2.set_controls({"AfMode": controls.AfModeEnum.Auto})
            # self.camera_mgr.picam2.set_controls({"AfTrigger": controls.AfTriggerEnum.Start})

            # time.sleep(1.0)  # 等待對焦完成

            # ## 曝光控制：設置曝光時間和增益
            # try:
            #     self.camera_mgr.picam2.set_controls({
            #         "AeEnable": 0,                 # 關閉自動曝光
            #         "ExposureTime": 10000,          # 曝光時間10毫秒
            #         "AnalogueGain": 2.0             # 調整增益來補償短曝光時間
            #     })
            #     logging.info("曝光時間成功設置為 10 毫秒 (10000 微秒)")
            # except Exception as e:
            #     logging.error(f"設置曝光時間時發生錯誤: {str(e)}")
            
            # # 執行拍照
            # logging.info("自動對焦完成，準備拍照...")
            self.state = State.CAPTURE

        elif self.key_mgr.check_key_pressed(self.display_mgr.disp.GPIO_KEY3_PIN):  # 查看圖片模式
            self.state = State.VIEW_IMAGE
            self.image_index = len(self.image_paths) - 1
    
    def handle_capture_state(self):
        logging.info("開始拍照...")

        # 捕捉高解析度圖片並進行縮略圖生成
        high_res_image = self.camera_mgr.capture_high_res_image_to_memory()

        if high_res_image is not None:
            logging.info("拍攝成功，顯示黑屏效果...")

            # 顯示預先生成的黑色畫面 (無需附加文字)
            self.display_mgr.disp.ShowImage_CV(self.black_image)  # 使用黑色畫面刷新顯示器

            # 黑屏效果：使用精確的短暫延時，並繼續執行其他操作
            # time.sleep(0.01)  # 黑屏0.01 秒，這已經達到讓使用者感知的快速效果

            logging.info("黑屏完成，準備執行後台保存動作...")

            # 生成縮略圖並儲存於快取
            thumbnail = self.generate_thumbnail(high_res_image)
            self.thumbnail_cache[len(self.image_paths)] = thumbnail

            # 使用後台線程保存圖片以避免阻塞主線程
            def save_image_in_background(image, image_index):
                """於後台線程中保存圖片"""
                current_time = time.strftime("%Y%m%d_%H%M%S")
                image_path = os.path.join(self.save_dir, f"{current_time}.jpg")
                logging.info(f"保存圖片中... {image_path}")
                # 保存圖片
                cv2.imwrite(image_path, image)
                logging.info(f"圖片已保存至 {image_path}")

                # 保存後更新圖片索引和路徑
                self.image_paths = self._get_image_paths_sorted()
                self.image_index = len(self.image_paths) - 1

            # 啟動後台線程來保存圖片，讓主線程繼續運行
            background_thread = Thread(target=save_image_in_background, args=(high_res_image, len(self.image_paths)))
            background_thread.start()

            logging.info("後台保存中，返回到預覽模式...")
        else:
            logging.error("未捕捉到有效的圖片")

        # 返回到預覽模式
        self.state = State.PREVIEW

    def handle_view_image_state(self):
        # 第一次進入時，初始化圖片索引
        if self.image_index is None:
            self.image_index = len(self.image_paths) - 1

        # 預加載圖片
        self.preload_images_around(self.image_index)

        if self.image_index is not None:
            # 從快取中獲取當前的縮略圖
            if self.image_index in self.thumbnail_cache:
                image = self.thumbnail_cache[self.image_index]
            else:
                logging.error(f"無法從快取加載縮略圖，索引: {self.image_index}")
                return

            # 從圖片檔名解析日期和時間
            image_path = self.image_paths[self.image_index]
            filename = os.path.basename(image_path).split(".")[0]
            date_part = filename[:8]
            time_part = filename[9:]

            # 格式化日期和時間
            image_date = f"{date_part[:4]}/{int(date_part[4:6])}/{int(date_part[6:8])}"
            image_time = f"{time_part[:2]}:{time_part[2:4]}"

            # 當前圖片資訊 (圖片索引/總圖片數)
            total_images = len(self.image_paths)
            current_image_info = f"{self.image_index + 1}/{total_images}"

            # 獲取當前電池電量百分比
            battery_percentage = self.get_battery_percentage()

            # 顯示圖片、圖片資訊、時間、日期和電池電量
            self.display_mgr.display_image_with_state(image, current_image_info, date_text=image_date, time_text=image_time, battery_percentage=battery_percentage)

            # 左/右按鈕切換圖片
            if self.key_mgr.check_key_pressed(self.display_mgr.disp.GPIO_KEY_LEFT_PIN):
                if self.image_index > 0:
                    self.image_index -= 1
                    self.preload_images_around(self.image_index)
            elif self.key_mgr.check_key_pressed(self.display_mgr.disp.GPIO_KEY_RIGHT_PIN):
                if self.image_index < len(self.image_paths) - 1:
                    self.image_index += 1
                    self.preload_images_around(self.image_index)

            # 返回預覽模式
            if self.key_mgr.check_key_pressed(self.display_mgr.disp.GPIO_KEY2_PIN):
                self.state = State.PREVIEW

    def run(self):
        # 根據當前狀態處理不同的邏輯
        if self.state == State.PREVIEW:
            self.handle_preview_state()
        elif self.state == State.VIEW_IMAGE:
            self.handle_view_image_state()
        elif self.state == State.CAPTURE:
            self.handle_capture_state()