# key_manager.py

import time
from time import time as timer

class KeyManager:
    def __init__(self, disp):
        """
        初始化按鍵管理器。
        """
        self.disp = disp
        self.key_last_pressed_time = {
            disp.GPIO_KEY1_PIN: 0,
            disp.GPIO_KEY2_PIN: 0,
            disp.GPIO_KEY3_PIN: 0,
            disp.GPIO_KEY_LEFT_PIN: 0,
            disp.GPIO_KEY_RIGHT_PIN: 0,
            disp.GPIO_KEY_UP_PIN: 0,
            disp.GPIO_KEY_DOWN_PIN: 0,
        }

    def check_key_pressed(self, key_pin, debounce_delay=0.15):
        """
        檢查指定的 GPIO pin 是否已被按下，並進行防抖處理。
        """
        current_time = timer()
        if self.disp.digital_read(key_pin) == 1:  # 直接檢查 GPIO pin 狀態
            if (current_time - self.key_last_pressed_time[key_pin]) > debounce_delay:
                self.key_last_pressed_time[key_pin] = current_time
                return True
        return False