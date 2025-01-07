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
    def __init__(self, display_mgr, cam_mgr, key_mgr, battery_mgr, save_dir):
        self.display_mgr = display_mgr
        self.camera_mgr = cam_mgr
        self.key_mgr = key_mgr
        self.battery_mgr = battery_mgr
        self.state = State.PREVIEW
        self.save_dir = save_dir
        self.thumbnail_dir = os.path.join(self.save_dir, "thumbnails")  # 縮略圖存放路徑
        os.makedirs(self.thumbnail_dir, exist_ok=True)  # 確保縮略圖目錄存在
        self.image_paths = self._get_image_paths_sorted()
        self.image_index = None
        self.thumbnail_cache = {}  # 用來儲存縮略圖的快取
        self.preload_latest_image()

    def _get_image_paths_sorted(self):
        """從保存路徑中獲取圖像文件並按時間排序"""
        try:
            files = [os.path.join(self.save_dir, f) for f in os.listdir(self.save_dir) if f.endswith(".jpg")]
            files.sort(key=os.path.getctime)
            return files
        except Exception as e:
            logging.error(f"Failed to get image paths: {e}")
            return []

    def load_or_generate_thumbnail(self, image_path):
        """嘗試加載縮略圖，如果不存在就生成新的."""
        # 縮略圖文件以原始圖片名稱為基準存儲
        thumbnail_path = os.path.join(self.thumbnail_dir, os.path.basename(image_path))

        # 如果縮略圖已經存在，直接加載
        if os.path.exists(thumbnail_path):
            return cv2.imread(thumbnail_path)

        # 如果縮略圖不存在，生成縮略圖並存儲
        image = cv2.imread(image_path)
        if image is None:
            logging.error(f"Failed to load image: {image_path}")
            return None

        thumbnail = self.generate_thumbnail(image)
        cv2.imwrite(thumbnail_path, thumbnail)  # 將生成好的縮略圖保存至硬盤
        return thumbnail

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

    def generate_thumbnail(self, image, max_width=240, max_height=135):
        """生成縮略圖，將圖像的尺寸調整至最大為 240x135 並保存"""
        original_height, original_width = image.shape[:2]
        scale = min(max_width / original_width, max_height / original_height)
        new_size = (int(original_width * scale), int(original_height * scale))

        # 使用 OpenCV 進行縮放
        thumbnail_img = cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)
        return thumbnail_img

    def preload_images_around(self, image_index):
        """
        預加載當前圖片的前 20 張和後 20 張圖片，生成縮略圖。
        """
        # 1. 調整預加載範圍：前後 20 張
        max_cache_range = 20  # 前後加載 20 張圖片
        start_idx = max(0, image_index - max_cache_range)
        end_idx = min(len(self.image_paths), image_index + max_cache_range + 1)

        # 2. 釋放範圍外的圖片
        max_distance_for_cache = 50  # 設定距離為 50 張的範圍外圖片將被釋放
        for idx in list(self.thumbnail_cache):  # 遍歷快取所有索引
            if abs(idx - image_index) > max_distance_for_cache:  # 超過範圍的縮略圖釋放
                del self.thumbnail_cache[idx]

        # 3. 對當前範圍內的圖片進行預加載
        for idx in range(start_idx, end_idx):
            if idx not in self.thumbnail_cache:
                image_path = self.image_paths[idx]
                thumbnail = self.load_or_generate_thumbnail(image_path)  # 嘗試加載或生成縮略圖
                if thumbnail is not None:
                    self.thumbnail_cache[idx] = thumbnail  # 加載後緩存縮略圖

    def get_battery_percentage(self, update_interval=60):
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
        # 擷取原始影像 (預覽模式的影像猜測為 BGRA 格式)
        raw_image = self.camera_mgr.picam2.capture_array()

        # 獲取當前電池電量百分比 (由 BatteryManager 獲取，並且已自動處理更新周期)
        battery_percentage = self.battery_mgr.get_battery_percentage()

        # 獲取當前的日期和時間
        current_time = time.strftime("%H:%M:%S")  # Example format: 18:57:05
        current_date = time.strftime("%Y/%m/%d")  # Example format: 2024/11/03

        # # 顯示圖像、電池百分比、時間和日期
        # 顯示即時影像，狀態為 "Preview"，顯示時間、日期和電池電量
        self.display_mgr.display_image_with_state(raw_image, "Capture", date_text=current_date, time_text=current_time, battery_percentage=battery_percentage)

        # 處理按鍵輸入
        if self.key_mgr.check_key_pressed(self.display_mgr.disp.GPIO_KEY1_PIN):     # 拍照按鍵被按下
            self.state = State.CAPTURE

        elif self.key_mgr.check_key_pressed(self.display_mgr.disp.GPIO_KEY3_PIN):   # 查看圖片模式
            self.state = State.VIEW_IMAGE
            self.image_index = len(self.image_paths) - 1
    
    def handle_capture_state(self):
        # 捕捉高解析度圖片並進行縮略圖生成
        logging.info("開始拍照...")

        high_res_image = self.camera_mgr.capture_high_res_image_to_memory()

        if high_res_image is not None:
            logging.info("準備執行後台保存動作...")

            # 生成縮略圖並儲存於快取
            thumbnail = self.generate_thumbnail(high_res_image)
            self.thumbnail_cache[len(self.image_paths)] = thumbnail

            # 使用後台線程保存圖片以避免阻塞主線程
            def save_image_in_background(image, image_index):
                """於後台線程中保存圖片"""
                current_time = time.strftime("%Y%m%d_%H%M%S")
                image_path = os.path.join(self.save_dir, f"{current_time}.jpg")
                thumbnail_path = os.path.join(self.thumbnail_dir, os.path.basename(image_path))
                logging.info(f"保存圖片中... {image_path}")
                # 保存圖片
                cv2.imwrite(image_path, image)
                cv2.imwrite(thumbnail_path, thumbnail)
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
            battery_percentage = self.battery_mgr.get_battery_percentage()

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