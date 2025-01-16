# display_manager.py

import cv2
import numpy as np
import logging
from ST7789 import ST7789
import INA219

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

    def display_image_with_state(self, image, state_text, date_text=None, time_text=None, battery_percentage=None):
        """
        顯示圖片以及狀態，如日期、時間、電池電量。
        """
        try:
            if image is None or image.size == 0:
                raise ValueError("無效的影像數據")

            target_width, target_height = self.disp.width, self.disp.height

            # 強制轉換色彩方案: BGR -> RGB（如有必要）
            if image.shape[2] == 4:
                image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
            elif image.shape[2] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            # 圖片縮放以適應顯示器尺寸
            original_height, original_width = image.shape[:2]
            scale = min(target_width / original_width, 135 / original_height)
            new_size = (int(original_width * scale), int(original_height * scale))
            resized_image = cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)

            # 建立黑色背景
            processed_image = np.zeros((target_height, target_width, 3), dtype=np.uint8)
            start_x = (target_width - new_size[0]) // 2
            start_y = (135 - new_size[1]) // 2 + 52
            processed_image[start_y:start_y + new_size[1], start_x:start_x + new_size[0]] = resized_image

            # 添加文字資訊
            font = cv2.FONT_HERSHEY_COMPLEX
            font_color = (255, 255, 255)
            thickness = 1

            # 日期顯示：左上角
            if date_text:
                self._draw_text(processed_image, date_text, (10, 30), font, font_color, thickness, align="left")
            
            # 時間顯示：右上角
            if time_text:
                self._draw_text(processed_image, time_text, (target_width - 10, 30), font, font_color, thickness, align="right")
            
            # 狀態顯示：左下角
            self._draw_text(processed_image, state_text, (10, target_height - 10), font, font_color, thickness, align="left")

            # 顯示電池狀態：右下角
            if battery_percentage is not None:
                self.draw_battery(processed_image, battery_percentage, target_width, target_height)

            # 顯示處理後的圖片
            self.disp.ShowImage_CV(processed_image)

        except Exception as e:
            logging.error(f"Failed to display image: {e}")

    def draw_battery(self, canvas, battery_percentage, target_width, target_height):
        """
        通用的電池顯示邏輯，電池固定顯示在右下角。
        """
        battery_percentage = max(0, min(battery_percentage, 100))  # 限制電量範圍在 0-100%

        battery_width, battery_height = 70, 15
        battery_x = target_width - battery_width - 10
        battery_y = target_height - battery_height - 10

        # 繪製電池框架
        cv2.rectangle(canvas, (battery_x, battery_y), (battery_x + battery_width, battery_y + battery_height), (255, 255, 255), 2)
        
        # 計算電池填充區域
        filled_width = int(battery_percentage / 100 * battery_width)
        filled_color = (0, 255, 0) if battery_percentage > 60 else (255, 255, 0) if battery_percentage > 20 else (255, 0, 0)

        if filled_width > 0:
            cv2.rectangle(canvas, (battery_x, battery_y), (battery_x + filled_width, battery_y + battery_height), filled_color, -1)

    def _draw_text(self, canvas, text, position, font, color, thickness, align="left"):
        """
        在畫布上繪製文字，支持左對齊、右對齊。
        """
        text_size = cv2.getTextSize(text, font, 0.5, thickness)[0]
        if align == "right":
            position = (position[0] - text_size[0], position[1])
        elif align == "center":
            position = (position[0] - text_size[0] // 2, position[1])

        cv2.putText(canvas, text, position, font, 0.5, color, thickness)

    def clear_display(self):
        self.disp.clear()

    def close_display(self):
        self.disp.module_exit()
