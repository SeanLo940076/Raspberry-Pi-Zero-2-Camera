# state_machine.py

import logging
import os
import cv2

from enum import Enum
from display_manager import DisplayManager
from camera_manager import CameraManager
from key_manager import KeyManager

class State(Enum):
    PREVIEW = 1
    VIEW_IMAGE = 2
    CAPTURE = 3

class StateMachine:
    def __init__(self, disp, cam_mgr, key_mgr, save_dir):
        self.display_mgr = DisplayManager()
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
        # 顯示相機預覽
        raw_image = self.camera_mgr.picam2.capture_array()
        self.display_mgr.display_image_with_state(raw_image, "Preview")

        # 處理按鍵輸入
        if self.key_mgr.check_key_pressed(self.display_mgr.disp.GPIO_KEY1_PIN):  # 拍照
            self.state = State.CAPTURE
        elif self.key_mgr.check_key_pressed(self.display_mgr.disp.GPIO_KEY3_PIN):  # 查看圖片
            self.state = State.VIEW_IMAGE
            self.image_index = len(self.image_paths) - 1

    def handle_capture_state(self):
        # 拍攝一張高解析度圖片並保存
        image_path = self.camera_mgr.capture_high_res_image(self.save_dir)
        if image_path:
            self.image_paths = self._get_image_paths_sorted()
            self.image_index = len(self.image_paths) - 1
        self.state = State.VIEW_IMAGE

    def handle_view_image_state(self):
        if self.image_index is not None:
            image = cv2.imread(self.image_paths[self.image_index])
            self.display_mgr.display_image_with_state(image, "View Image")

            # 處理左右按鍵的輸入
            if self.key_mgr.check_key_pressed(self.display_mgr.disp.GPIO_KEY_LEFT_PIN):
                self.image_index = max(0, self.image_index - 1)
            elif self.key_mgr.check_key_pressed(self.display_mgr.disp.GPIO_KEY_RIGHT_PIN):
                self.image_index = min(len(self.image_paths) - 1, self.image_index + 1)
            elif self.key_mgr.check_key_pressed(self.display_mgr.disp.GPIO_KEY2_PIN):
                self.state = State.PREVIEW

    def run(self):
        if self.state == State.PREVIEW:
            self.handle_preview_state()
        elif self.state == State.VIEW_IMAGE:
            self.handle_view_image_state()
        elif self.state == State.CAPTURE:
            self.handle_capture_state()