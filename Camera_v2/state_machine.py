# state_machine.py

import logging
import os
import cv2
from enum import Enum
import time
from threading import Thread
from thumbnail_manager import ThumbnailManager
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
        self.thumbnail_mgr = ThumbnailManager(save_dir, os.path.join(save_dir, "thumbnails"))
        self.thumbnail_mgr.preload_thumbnails()
        self.image_index = None

    def handle_preview_state(self):
        raw_image = self.camera_mgr.picam2.capture_array()

        if raw_image is None or raw_image.size == 0:
            logging.error("預覽模式下捕捉到無效影像")
            return

        battery_percentage = self.battery_mgr.get_battery_percentage()

        current_time = time.strftime("%H:%M:%S")
        current_date = time.strftime("%Y/%m/%d")

        self.display_mgr.display_image_with_state(raw_image, "Capture", date_text=current_date, time_text=current_time, battery_percentage=battery_percentage)

        if self.key_mgr.check_key_pressed(self.display_mgr.disp.GPIO_KEY1_PIN):
            self.state = State.CAPTURE

        elif self.key_mgr.check_key_pressed(self.display_mgr.disp.GPIO_KEY3_PIN):
            self.state = State.VIEW_IMAGE
            self.image_index = len(self.thumbnail_mgr.image_paths) - 1

    def handle_capture_state(self):
        logging.info("開始拍照...")

        high_res_image = self.camera_mgr.capture_high_res_image_to_memory()

        if high_res_image is not None:
            def save_image_and_thumbnail(image):
                current_time = time.strftime("%Y%m%d_%H%M%S")
                image_path = os.path.join(self.thumbnail_mgr.save_dir, f"{current_time}.jpg")
                if cv2.imwrite(image_path, image):
                    self.thumbnail_mgr.update_image_list()
                    logging.info(f"圖片已保存: {image_path}")
                else:
                    logging.error(f"保存圖片失敗: {image_path}")

            Thread(target=save_image_and_thumbnail, args=(high_res_image,)).start()
            logging.info("後台保存中，返回到預覽模式...")
        else:
            logging.error("未捕捉到有效的圖片")

        self.state = State.PREVIEW

    def handle_view_image_state(self):
        if self.image_index is None:
            self.image_index = len(self.thumbnail_mgr.image_paths) - 1

        if self.image_index is not None:
            image_path = self.thumbnail_mgr.image_paths[self.image_index]
            image = self.thumbnail_mgr.load_or_generate_thumbnail(image_path)

            if image is None:
                logging.error(f"無法加載圖片: {image_path}")
                return

            filename = os.path.basename(image_path).split(".")[0]
            date_part = filename[:8]
            time_part = filename[9:]

            # 保證日期格式統一為 YYYY/MM/DD，並包含秒數
            image_date = f"{date_part[:4]}/{date_part[4:6]:0>2}/{date_part[6:8]:0>2}"
            image_time = f"{time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"

            total_images = len(self.thumbnail_mgr.image_paths)
            current_image_info = f"{self.image_index + 1}/{total_images}"

            battery_percentage = self.battery_mgr.get_battery_percentage()

            self.display_mgr.display_image_with_state(image, current_image_info, date_text=image_date, time_text=image_time, battery_percentage=battery_percentage)

            if self.key_mgr.check_key_pressed(self.display_mgr.disp.GPIO_KEY_LEFT_PIN):
                if self.image_index > 0:
                    self.image_index -= 1
            elif self.key_mgr.check_key_pressed(self.display_mgr.disp.GPIO_KEY_RIGHT_PIN):
                if self.image_index < len(self.thumbnail_mgr.image_paths) - 1:
                    self.image_index += 1

            if self.key_mgr.check_key_pressed(self.display_mgr.disp.GPIO_KEY2_PIN):
                self.state = State.PREVIEW

    def run(self):
        if self.state == State.PREVIEW:
            self.handle_preview_state()
        elif self.state == State.VIEW_IMAGE:
            self.handle_view_image_state()
        elif self.state == State.CAPTURE:
            self.handle_capture_state()
