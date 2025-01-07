# main.py

import os
import logging
from camera_manager import CameraManager
from key_manager import KeyManager
from display_manager import DisplayManager
from state_machine import StateMachine
from battery_manager import BatteryManager

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # 初始化顯示器
    disp_mgr = DisplayManager()
    if disp_mgr.disp:
        # 初始化電池管理器
        battery_mgr = BatteryManager(update_interval=60)

        # 初始化相機管理器
        cam_mgr = CameraManager(disp_mgr)

        if cam_mgr.initialize_camera():
            key_mgr = KeyManager(disp_mgr.disp)

            # 創建目錄來保存照片
            save_dir = "/home/SeanPi-2w/camera_1102/photo/"
            os.makedirs(save_dir, exist_ok=True)

            # 初始化狀態機
            state_machine = StateMachine(disp_mgr, cam_mgr, key_mgr, battery_mgr, save_dir)

            # 主循環 - 使用狀態機來處理相機流程
            try:
                while True:
                    state_machine.run()  # 狀態機的運行邏輯
            except KeyboardInterrupt:
                logging.info("程序被用戶中斷。")
                cam_mgr.close_camera()
                disp_mgr.close_display()
        else:
            logging.error("相機初始化失敗。")
    else:
        logging.error("顯示初始化失敗。")