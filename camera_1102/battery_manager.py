import logging
import time
from INA219 import INA219

class BatteryManager:
    def __init__(self, update_interval=60):
        logging.info("Initializing battery sensor...")
        try:
            # 初始化 INA219 感側器（假設其在 I2C 地址 0x43）
            self.ina219 = INA219(addr=0x43)
            logging.info("INA219 電池感測器初始化成功。")
        except Exception as e:
            logging.error(f"無法初始化 INA219 電池感測器: {e}")
            self.ina219 = None

        self.last_battery_percentage = None
        self.last_update_time = 0
        self.update_interval = update_interval
    
    def get_battery_percentage(self):
        """取得電池百分比並根據時間間隔來更新，目前是60秒。"""
        current_time = time.time()

        if (current_time - self.last_update_time) >= self.update_interval:
            try:
                if self.ina219:
                    bus_voltage = self.ina219.getBusVoltage_V()

                    # 將最高電壓設為 3.9V，而不是 4.2V，這樣電池看起來能更多接近 100%
                    battery_percentage = (bus_voltage - 3.0) / (4.0 - 3.0) * 100  # 假設電壓範圍為 3.0V ~ 4.0V
                    battery_percentage = max(0, min(100, battery_percentage))  # 限定在 0~100%

                    self.last_battery_percentage = battery_percentage
                    self.last_update_time = current_time
                    logging.info(f"Battery percentage updated: {battery_percentage:.2f}%")
            except Exception as e:
                logging.error(f"Error reading battery percentage: {e}")
                self.last_battery_percentage = None

        return self.last_battery_percentage