# main.py

import os
import logging
from camera_manager import CameraManager
from key_manager import KeyManager
from state_machine import StateMachine
from display_manager import DisplayManager
import config  # 載入硬件配置

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # 初始化顯示器
    display_mgr = DisplayManager()
    if display_mgr.disp:
        cam_mgr = CameraManager()
        if cam_mgr.initialize_camera():
            # 指定按鍵的引腳映射
            key_pins = {
                'KEY1': config.KEY1_PIN,
                'KEY2': config.KEY2_PIN,
                'KEY3': config.KEY3_PIN,
                'KEY_LEFT': config.KEY_LEFT_PIN,
                'KEY_RIGHT': config.KEY_RIGHT_PIN
            }

            # 初始化按鍵管理器
            key_mgr = KeyManager(display_mgr.disp, key_pins)
            save_dir = "/home/SeanPi-2w/camera_1102/photo/"
            os.makedirs(save_dir, exist_ok=True)

            # 創建相機狀態機並運行
            state_machine = StateMachine(display_mgr.disp, cam_mgr, key_mgr, save_dir)

            try:
                while True:
                    state_machine.run()
            except KeyboardInterrupt:
                logging.info("Program interrupted by user.")
                cam_mgr.close_camera()
                display_mgr.close_display()
        else:
            logging.error("Camera initialization failed.")
    else:
        logging.error("Display initialization failed.")