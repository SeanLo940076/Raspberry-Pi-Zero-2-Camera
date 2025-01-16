# display_manager.py

import cv2
import numpy as np
import logging
from ST7789 import ST7789
import INA219
import time

class DisplayManager:
    def __init__(self):
        logging.info("Initializing display...")
        try:
            self.disp = ST7789()
            self.disp.Init()
            self.disp.clear()
            self.disp.bl_DutyCycle(100)
            logging.info("Display initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize display: {e}")
            self.disp = None

        self.cached_battery_image = None  # 快取的電池圖案
        self.last_battery_percentage = None  # 上次的電量百分比
        self.cached_date_layer = None  # 快取日期文字層
        self.last_date_text = None  # 上次的日期文字

        # 用於計算 FPS 的變量
        self.last_frame_time = time.time()
        self.frame_count = 0
        self.fps = 0

    def display_image_with_state(self, image, state_text, date_text=None, time_text=None, battery_percentage=None):
        """
        顯示圖片以及狀態，如日期、時間、電池電量。
        """
        try:
            if image is None or image.size == 0:
                raise ValueError("無效的影像數據")

            # 強制轉換色彩方案: BGR -> RGB（如有必要）
            if image.shape[2] == 4:
                image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
            elif image.shape[2] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            target_width, target_height = self.disp.width, self.disp.height

            # 圖片縮放
            original_height, original_width = image.shape[:2]
            scale = min(target_width / original_width, 135 / original_height)
            new_size = (int(original_width * scale), int(original_height * scale))
            resized_image = cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)

            # 建立黑色背景
            processed_image = np.zeros((target_height, target_width, 3), dtype=np.uint8)
            start_x = (target_width - resized_image.shape[1]) // 2
            start_y = (135 - resized_image.shape[0]) // 2 + 52
            processed_image[start_y:start_y + resized_image.shape[0], start_x:start_x + resized_image.shape[1]] = resized_image

            # 日期文字（僅當日期改變時更新）
            if date_text != self.last_date_text:
                self.last_date_text = date_text
                self.cached_date_layer = self._generate_text_layer(date_text, (10, 30), font_size=0.5, align="left")

            # 疊加日期文字層
            if self.cached_date_layer is not None:
                processed_image = cv2.addWeighted(processed_image, 1.0, self.cached_date_layer, 1.0, 0)

            # 時間文字（每次都更新）
            if time_text:
                self._draw_text(processed_image, time_text, (target_width - 10, 30), cv2.FONT_HERSHEY_COMPLEX, (255, 255, 255), 1, align="right")

            # 狀態文字
            self._draw_text(processed_image, state_text, (10, target_height - 10), cv2.FONT_HERSHEY_COMPLEX, (255, 255, 255), 1, align="left")

            # 電池圖案（僅當電量變化時更新）
            if battery_percentage != self.last_battery_percentage:
                self.last_battery_percentage = battery_percentage
                self.cached_battery_image = self._generate_battery_image(battery_percentage)

            # 疊加電池圖案，應用位置偏移
            if self.cached_battery_image is not None:
                x_start = target_width - self.cached_battery_image.shape[1] - 10  # 向左移動 10 pixels
                y_start = target_height - self.cached_battery_image.shape[0] - 5  # 向上移動 10 pixels
                processed_image[y_start:y_start + self.cached_battery_image.shape[0], x_start:x_start + self.cached_battery_image.shape[1]] = self.cached_battery_image

            # 計算 FPS
            self.frame_count += 1
            current_time = time.time()
            elapsed_time = current_time - self.last_frame_time
            if elapsed_time >= 1.0:  # 每秒更新一次 FPS
                self.fps = self.frame_count / elapsed_time
                self.frame_count = 0
                self.last_frame_time = current_time

            # 在左下角顯示 FPS
            self._draw_text(processed_image, f"FPS: {self.fps:.2f}", (10, target_height - 30), cv2.FONT_HERSHEY_COMPLEX, (0, 255, 0), 1, align="left")

            # 顯示處理後的圖片
            self.disp.ShowImage_CV(processed_image)

        except Exception as e:
            logging.error(f"Failed to display image: {e}")

    def _generate_text_layer(self, text, position, font_size=0.5, font=cv2.FONT_HERSHEY_COMPLEX, align="left"):
        """
        生成靜態文字圖層。
        """
        layer = np.zeros((self.disp.height, self.disp.width, 3), dtype=np.uint8)
        self._draw_text(layer, text, position, font, (255, 255, 255), 1, align)
        return layer

    def _generate_battery_image(self, battery_percentage):
        """
        生成電池圖案，僅當電量變化時調用。
        """
        battery_percentage = max(0, min(battery_percentage, 100))  # 限制電量範圍在 0-100%

        battery_width, battery_height = 70, 15
        battery_image = np.zeros((battery_height, battery_width, 3), dtype=np.uint8)

        # 繪製電池框架
        cv2.rectangle(battery_image, (0, 0), (battery_width, battery_height), (255, 255, 255), 2)
        
        # 計算電池填充顏色
        filled_width = int(battery_percentage / 100 * battery_width)
        filled_color = (0, 255, 0) if battery_percentage > 60 else (255, 255, 0) if battery_percentage > 20 else (255, 0, 0)

        if filled_width > 0:
            cv2.rectangle(battery_image, (0, 0), (filled_width, battery_height), filled_color, -1)

        return battery_image

    def _draw_text(self, canvas, text, position, font, color, thickness, align="left"):
        """
        在畫布上繪製文字，支持左對齊、右對齊。
        """
        text_size = cv2.getTextSize(text, font, fontScale=0.5, thickness=thickness)[0]
        if align == "right":
            position = (position[0] - text_size[0], position[1])
        elif align == "center":
            position = (position[0] - text_size[0] // 2, position[1])

        cv2.putText(canvas, text, position, font, 0.5, color, thickness)

    def clear_display(self):
        self.disp.clear()

    def close_display(self):
        self.disp.module_exit()