# display_manager.py
import logging
import cv2
import numpy as np
from ST7789 import ST7789  # 引入提供的 ST7789 繪圖驅動

class DisplayManager:
    def __init__(self):
        logging.info("Initializing display...")
        try:
            self.disp = ST7789()
            self.disp.Init()
            self.disp.clear()
            logging.info("Display initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize display: {e}")
            self.disp = None

    def display_image_with_state(self, image, state_text):
        try:
            # 確保圖像大小匹配顯示器的尺寸 (240x240)
            imheight, imwidth = image.shape[:2]

            if imwidth != self.disp.width or imheight != self.disp.height:
                raise ValueError('Image must be the same dimensions as display \
                    ({0}x{1}).'.format(self.disp.width, self.disp.height))

            # 添加狀態文本
            cv2.putText(image, state_text, (10, 230), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (255, 255, 255), 1, cv2.LINE_AA)

            # 顯示圖片 (使用 ST7789 驅動)
            self.disp.ShowImage_CV(image)
        except Exception as e:
            logging.error(f"Failed to display image: {e}")

    def clear_display(self):
        self.disp.clear()

    def close_display(self):
        self.disp.module_exit()