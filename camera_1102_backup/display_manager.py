# display_manager.py

import cv2
import numpy as np
import logging
from ST7789 import ST7789  # 引入現有的 ST7789 驅動程式

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

    def display_image_with_state(self, image, state_text, date_text=None, time_text=None):
        try:
            # 確定顯示區域大小
            target_width = self.disp.width
            target_height = self.disp.height

            # 強制轉換色彩方案: BGR -> RGB，如果圖像有3個通道(BGR)
            if image.shape[2] == 4:
                image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
            # elif image.shape[2] == 3:
            #     image = cv2.cvtColor(image, cv2.COLOR_BGR2BGR)

            # 圖像縮放以適應顯示器
            original_height, original_width = image.shape[:2]
            scale = min(target_width / original_width, 135 / original_height)
            new_size = (int(original_width * scale), int(original_height * scale))
            resized_image = cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)

            # 黑色背景圖像，並將縮放後的圖像置於背景中央
            processed_image = np.zeros((target_height, target_width, 3), dtype=np.uint8)
            start_x = (target_width - new_size[0]) // 2
            start_y = (135 - new_size[1]) // 2 + 52  # Y 偏移，將圖放置在中心

            processed_image[start_y:start_y + new_size[1], start_x:start_x + new_size[0]] = resized_image

            # 設定字體和大小
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_color = (255, 255, 255)  # 白色
            thickness = 1  # 字體厚度

            # 在圖片顶部显示日期與時間 (日期位於左上角, 時間位於右上角)
            if date_text:
                cv2.putText(processed_image, date_text, (10, 30), font, 0.5, font_color, thickness)
            if time_text:
                cv2.putText(processed_image, time_text, (target_width - 100, 30), font, 0.5, font_color, thickness)

            # 在圖片的左下角顯示狀態文字(如預覽、拍照、相簿)
            cv2.putText(processed_image, state_text, (10, target_height - 10), font, 0.6, font_color, thickness)

            # 顯示圖像
            self.disp.ShowImage_CV(processed_image)

        except Exception as e:
            logging.error(f"Failed to display image: {e}")

    def clear_display(self):
        self.disp.clear()

    def close_display(self):
        self.disp.module_exit()