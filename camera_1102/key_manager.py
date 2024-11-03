# key_manager.py

import time
from time import time as timer
import logging
from ST7789 import ST7789 

class KeyManager:
    def __init__(self, disp, key_pins):
        """
        初始化按鍵管理器。
        :param disp: ST7789 display 對象，包含了 GPIO 操作
        :param key_pins: 字典，包含各個對應的 GPIO pins
        """
        self.disp = disp
        self.key_pins = key_pins
        self.key_last_pressed_time = {pin: 0 for pin in key_pins.values()}

    def check_key_pressed(self, key_name, debounce_delay=0.2):
        """
        檢查指定的按鍵是否已被按下，並進行 debounce 處理。
        :param key_name: 指定的按鍵名稱（key_pins 字典中的鍵）
        :param debounce_delay: 去抖動的延遲時間
        :return: 如果按鍵被按下且已經 debounce，返回 True，否則 False
        """
        key_pin = self.key_pins[key_name]
        current_time = timer()

        # 從 display 中檢查 GPIO 對應的狀態
        if self.disp.digital_read(key_pin) == 1:
            if (current_time - self.key_last_pressed_time[key_pin]) > debounce_delay:
                self.key_last_pressed_time[key_pin] = current_time
                return True
        return False