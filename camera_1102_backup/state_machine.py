# state_machine.py

import logging
import os
import cv2
from enum import Enum
import time  # 確保引入 time 模組以使用 delay 功能

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
        self.image_paths = self._get_image_paths_sorted()
        self.image_index = None

    def _get_image_paths_sorted(self):
        try:
            files = [os.path.join(self.save_dir, f) for f in os.listdir(self.save_dir) if f.endswith(".jpg")]
            files.sort(key=os.path.getctime)
            return files
        except Exception as e:
            logging.error(f"Failed to get image paths: {e}")
            return []

    def handle_preview_state(self):
        # 擷取原始影像 (可能是 BGR 格式)
        raw_image = self.camera_mgr.picam2.capture_array()
        # # 將 BGR 轉換為 RGB
        # if raw_image.shape[2] == 3:
        #     raw_image = cv2.cvtColor(raw_image, cv2.COLOR_BGR2RGB)
        
        self.display_mgr.display_image_with_state(raw_image, "Preview")

        # 處理按鍵輸入
        if self.key_mgr.check_key_pressed(self.display_mgr.disp.GPIO_KEY1_PIN):  # 拍照按鍵
            self.state = State.CAPTURE
        elif self.key_mgr.check_key_pressed(self.display_mgr.disp.GPIO_KEY3_PIN):  # 查看圖片模式按鍵
            self.state = State.VIEW_IMAGE
            self.image_index = len(self.image_paths) - 1

    def handle_capture_state(self):
        # 拍攝一張高解析度圖片並保存
        image_path = self.camera_mgr.capture_high_res_image(self.save_dir)
        if image_path:
            self.image_paths = self._get_image_paths_sorted()  # 更新圖片列表
            self.image_index = len(self.image_paths) - 1
        self.state = State.PREVIEW

    def handle_view_image_state(self):
        if self.image_index is not None:
            # 讀取當前圖像
            image_path = self.image_paths[self.image_index]
            image = cv2.imread(image_path)

            # 解析圖片檔名來獲取日期與時間，例如 "20241103_103739.jpg"
            filename = os.path.basename(image_path).split(".")[0]  # 取得不帶副檔名的文件名
            date_part = filename[:8]  # "20241103"
            time_part = filename[9:]  # "103739"

            # 格式化日期與時間
            image_date = f"{date_part[:4]}/{int(date_part[4:6])}/{int(date_part[6:8])}"  # "2024/11/3"
            image_time = f"{time_part[:2]}:{time_part[2:4]}"  # "10:37"
            
            # 總數量與當前索引顯示
            total_images = len(self.image_paths)
            current_image_info = f"{self.image_index + 1}/{total_images}"  # 例如 "3/5"

            # 調用 display_image_with_state 顯示圖片與信息
            self.display_mgr.display_image_with_state(image, current_image_info, date_text=image_date, time_text=image_time)

            # 處理左右按鍵的輸入
            if self.key_mgr.check_key_pressed(self.display_mgr.disp.GPIO_KEY_LEFT_PIN):  # 切換到上一張圖片
                self.image_index = max(0, self.image_index - 1)
            elif self.key_mgr.check_key_pressed(self.display_mgr.disp.GPIO_KEY_RIGHT_PIN):  # 切換到下一張圖片
                self.image_index = min(len(self.image_paths) - 1, self.image_index + 1)
            elif self.key_mgr.check_key_pressed(self.display_mgr.disp.GPIO_KEY2_PIN):  # 返回預覽模式
                self.state = State.PREVIEW

    def run(self):
        # 根據當前狀態處理不同的邏輯
        if self.state == State.PREVIEW:
            self.handle_preview_state()
        elif self.state == State.VIEW_IMAGE:
            self.handle_view_image_state()
        elif self.state == State.CAPTURE:
            self.handle_capture_state()