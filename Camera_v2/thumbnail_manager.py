# thumbnail_manager.py

import os
import cv2
import logging
from threading import Thread

class ThumbnailManager:
    def __init__(self, save_dir, thumbnail_dir):
        self.save_dir = save_dir
        self.thumbnail_dir = thumbnail_dir
        os.makedirs(self.thumbnail_dir, exist_ok=True)
        self.image_paths = self._get_image_paths_sorted()
        self.thumbnail_cache = {}

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
        """嘗試加載縮略圖，如果不存在就生成新的。"""
        thumbnail_path = os.path.join(self.thumbnail_dir, os.path.basename(image_path))
        if os.path.exists(thumbnail_path):
            return cv2.imread(thumbnail_path)

        image = cv2.imread(image_path)
        if image is None or image.size == 0:
            logging.error(f"Failed to load image: {image_path}")
            return None

        thumbnail = self.generate_thumbnail(image)
        cv2.imwrite(thumbnail_path, thumbnail)
        return thumbnail

    def generate_thumbnail(self, image, max_width=240, max_height=135):
        """生成縮略圖，將圖像的尺寸調整至最大為 240x135"""
        original_height, original_width = image.shape[:2]
        scale = min(max_width / original_width, max_height / original_height)
        new_size = (int(original_width * scale), int(original_height * scale))
        return cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)

    def preload_thumbnails(self):
        """後台檢查並生成缺少的縮略圖"""
        def check_and_generate():
            for image_path in self.image_paths:
                thumbnail_path = os.path.join(self.thumbnail_dir, os.path.basename(image_path))
                if not os.path.exists(thumbnail_path):
                    self.load_or_generate_thumbnail(image_path)

        Thread(target=check_and_generate, daemon=True).start()

    def update_image_list(self):
        """更新影像清單並檢查是否有新的縮略圖需要生成"""
        self.image_paths = self._get_image_paths_sorted()
        self.preload_thumbnails()
