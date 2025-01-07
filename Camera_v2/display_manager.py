# display_manager.py

import cv2
import numpy as np
import logging
from ST7789 import ST7789  # 引入現有的 ST7789 驅動程式
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
            # 確定顯示區域大小
            target_width = self.disp.width
            target_height = self.disp.height

            # 強制轉換色彩方案: BGR -> RGB（如有必要）
            if image.shape[2] == 4:
                image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
            elif image.shape[2] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            # 圖片縮放，以適應顯示器的尺寸
            original_height, original_width = image.shape[:2]
            scale = min(target_width / original_width, 135 / original_height)
            new_size = (int(original_width * scale), int(original_height * scale))
            resized_image = cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)

            # 黑色的背景圖像，中央放置縮放後的圖片
            processed_image = np.zeros((target_height, target_width, 3), dtype=np.uint8)
            start_x = (target_width - new_size[0]) // 2
            start_y = (135 - new_size[1]) // 2 + 52  # Y 偏移，確保居中對齊

            processed_image[start_y:start_y + new_size[1], start_x:start_x + new_size[0]] = resized_image

            # 設定字體和大小
            font = cv2.FONT_HERSHEY_COMPLEX
            font_color = (255, 255, 255)  # 白色字體
            thickness = 1  # 字體厚度

            # 顯示頂部的日期和時間 (左上角顯示日期, 右上角顯示時間)
            if date_text:
                cv2.putText(processed_image, date_text, (10, 30), font, 0.5, font_color, thickness)
            if time_text:
                cv2.putText(processed_image, time_text, (target_width - 100, 30), font, 0.5, font_color, thickness)

            # 左下角顯示狀態 (state_text 比如顯示 "預覽", "拍照", "相簿")
            cv2.putText(processed_image, state_text, (10, target_height - 10), font, 0.6, font_color, thickness)

            # 顯示電池狀態欄
            if battery_percentage is not None:
                self.draw_battery(processed_image, battery_percentage, target_width, target_height)

            # 顯示最終處理的圖像
            self.disp.ShowImage_CV(processed_image)

        except Exception as e:
            logging.error(f"Failed to display image: {e}")

    def draw_battery(self, canvas, battery_percentage, target_width, target_height):
        """
        通用的電池顯示邏輯。根據 battery_percentage 決定顏色
        60% 以下將設為黃色，20% 以下為紅色，其他情況為綠色。
        """
        # 電池圖形顯示區域，右下角
        battery_x = target_width - 100
        battery_y = target_height - 30
        battery_width = 80
        battery_height = 20

        # 畫出空的電池框架
        cv2.rectangle(canvas, (battery_x, battery_y), (battery_x + battery_width, battery_y + battery_height), (255, 255, 255), 2)

        # 根據電池百分比填充狀態條
        filled_width = int(battery_percentage / 100 * battery_width)

        # 根據不同電量設置不同顏色：
        if battery_percentage > 60:
            filled_color = (0, 255, 0)   # 綠色，表示充足
        elif battery_percentage > 20:
            filled_color = (255, 255, 0) # 黃色，表示電量較低
        else:
            filled_color = (255, 0, 0)   # 紅色，表示電量非常低

        # 繪製完成的電池狀態條
        cv2.rectangle(canvas, (battery_x, battery_y), (battery_x + filled_width, battery_y + battery_height), filled_color, -1)

    def display_battery(self, canvas, battery_percentage):
        """
        單純顯示電池圖示。
        """
        self.draw_battery(canvas, battery_percentage, self.disp.width, self.disp.height)
        return canvas

    def clear_display(self):
        self.disp.clear()

    def close_display(self):
        self.disp.module_exit()