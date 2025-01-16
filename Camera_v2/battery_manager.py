# battery_manager.py

import logging
import time
from INA219 import INA219

class BatteryManager:
    def __init__(self, update_interval=60):
        logging.info("Initializing battery sensor...")
        try:
            self.ina219 = INA219(addr=0x43)
            logging.info("INA219 電池感測器初始化成功。")
        except Exception as e:
            logging.error(f"無法初始化 INA219 電池感測器: {e}")
            self.ina219 = None

        self.last_battery_percentage = None
        self.last_update_time = 0
        self.update_interval = update_interval

    def get_battery_percentage(self):
        """取得電池百分比，僅在設定時間間隔內更新數據，其餘時間返回快取值。"""
        current_time = time.time()

        # 如果未達到更新間隔，直接返回快取值
        if (current_time - self.last_update_time) < self.update_interval:
            return self.last_battery_percentage

        # 嘗試更新電量數據
        try:
            if self.ina219:
                bus_voltage = self.ina219.getBusVoltage_V()
                battery_percentage = (bus_voltage - 3.0) / (4.0 - 3.0) * 100
                battery_percentage = max(0, min(100, battery_percentage))  # 限定在 0~100%
                self.last_battery_percentage = battery_percentage
                self.last_update_time = current_time
                logging.info(f"Battery percentage updated: {battery_percentage:.2f}%")
            else:
                if self.last_battery_percentage is None:
                    logging.warning("INA219 未初始化，無法獲取電池電量。")
        except Exception as e:
            logging.error(f"無法取得電池百分比: {e}")
            self.last_battery_percentage = None

        return self.last_battery_percentage

    def is_battery_low(self, threshold=20):
        """檢查電池電量是否低於設定的閾值。"""
        if self.last_battery_percentage is not None:
            return self.last_battery_percentage < threshold
        logging.warning("無法檢查電池狀態，電量數據為空。")
        return False