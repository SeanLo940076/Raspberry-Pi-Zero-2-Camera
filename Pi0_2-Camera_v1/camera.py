# Author: Yu-Hsiang Lo
# Date: August 2024
# Project Name: Raspberry Pi0-2w Camera

import spidev as SPI
import logging
import ST7789
import time
import cv2
from picamera2 import Picamera2, Preview
from time import time as timer
import os
from enum import Enum
import numpy as np

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define state enumeration class
class State(Enum):
    PREVIEW = 1
    VIEW_IMAGE = 2
    CAPTURE = 3

# Initialize the display
def initialize_display():
    logging.info("Initializing display...")
    try:
        disp = ST7789.ST7789()
        disp.Init()
        disp.clear()
        disp.bl_DutyCycle(100)
        logging.info("Display initialized and backlight set to 100%.")
        return disp
    except Exception as e:
        logging.error(f"Failed to initialize display: {e}")
        return None

def initialize_camera():
    logging.info("Initializing camera...")
    try:
        picam2 = Picamera2()
        mode1 = picam2.sensor_modes[1]
        mode2 = picam2.sensor_modes[2]
        preview_config = picam2.create_video_configuration(sensor={'output_size': mode1['size'],
                                                                   'bit_depth': mode1['bit_depth']})
        capture_config = picam2.create_still_configuration(sensor={'output_size': mode2['size'],
                                                                   'bit_depth': mode2['bit_depth']})
        picam2.configure(preview_config)
        picam2.start_preview(Preview.NULL)  # Use a null preview to keep the camera initialized
        picam2.start()
        logging.info("Camera initialized and ready.")

        # Capture and discard the first image to ensure proper camera initialization
        logging.info("Capturing and discarding the first image to stabilize the camera.")
        _ = picam2.switch_mode_and_capture_array(capture_config)

        return picam2, capture_config
    except Exception as e:
        logging.error(f"Failed to initialize camera: {e}")
        return None, None


# Display image with state text
def display_image_with_state(disp, image, state_text):
    try:
        target_width = disp.width
        target_height = disp.height

        # Force conversion of the image to RGB format, whether it is BGR or BGRA
        if image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        elif image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Scale and resize the image to fit within the 240x135 area
        original_height, original_width = image.shape[:2]
        scale = min(240 / original_width, 135 / original_height)
        new_size = (int(original_width * scale), int(original_height * scale))
        resized_image = cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)

        # Create a black background image (3 channels) with 240x240 resolution
        processed_image = np.zeros((240, 240, 3), dtype=np.uint8)

        # Calculate the starting position to paste the image in the center
        start_x = (240 - new_size[0]) // 2
        start_y = (135 - new_size[1]) // 2 + 52  # Center in the 240x135 region

        # Paste the resized image onto the background image
        processed_image[start_y:start_y + new_size[1], start_x:start_x + new_size[0]] = resized_image

        # Add state text at the bottom of the display (aligned to the bottom of the 240x135 area)
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(processed_image, state_text, (10, 230), font, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

        disp.ShowImage_CV(processed_image)
    except Exception as e:
        logging.error(f"Failed to display image: {e}")

# Show live preview with state text
def show_live_preview(disp, picam2, state_text):
    try:
        raw_image = picam2.capture_array()

        # Process and display the image with state text
        display_image_with_state(disp, raw_image, state_text)
    except Exception as e:
        logging.error(f"Failed to show live preview: {e}")

# Get image file paths sorted by time
def get_image_paths_sorted(directory):
    try:
        files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".jpg")]
        files.sort(key=os.path.getctime)  # Sort by file creation time
        return files
    except Exception as e:
        logging.error(f"Failed to get image paths: {e}")
        return []

# Key debounce state record
def initialize_key_state():
    return {
        disp.GPIO_KEY1_PIN: 0,
        disp.GPIO_KEY2_PIN: 0,
        disp.GPIO_KEY3_PIN: 0,
        disp.GPIO_KEY_LEFT_PIN: 0,
        disp.GPIO_KEY_RIGHT_PIN: 0,
    }

# Check if a key is pressed with debounce logic
def check_key_pressed(disp, key_pin, key_last_pressed_time, debounce_delay=0.2):
    current_time = timer()
    if disp.digital_read(key_pin) == 1:
        if (current_time - key_last_pressed_time[key_pin]) > debounce_delay:
            key_last_pressed_time[key_pin] = current_time
            return True
    return False

# Display the latest image with state text
def display_latest_image(disp, save_dir, state_text):
    try:
        image_paths = get_image_paths_sorted(save_dir)
        if image_paths:
            latest_image = cv2.imread(image_paths[-1])
            display_image_with_state(disp, latest_image, state_text)
            return len(image_paths) - 1  # Return the index of the latest image
        else:
            logging.warning("No saved images found.")
            return None
    except Exception as e:
        logging.error(f"Failed to display the latest image: {e}")
        return None

# Capture and display an image with state text
def capture_and_display_image(disp, picam2, capture_config, save_dir, state_text):
    logging.info("Capturing high resolution image...")
    try:
        high_res_image = picam2.switch_mode_and_capture_array(capture_config)

        # Convert BGR to RGB before displaying the image
        high_res_image_rgb = cv2.cvtColor(high_res_image, cv2.COLOR_BGR2RGB)
        display_image_with_state(disp, high_res_image_rgb, state_text)

        # Generate filename to save the image
        current_time = time.strftime("%Y%m%d_%H%M%S")
        image_path = os.path.join(save_dir, f"{current_time}.jpg")

        # Save the image as an RGB JPG file
        cv2.imwrite(image_path, high_res_image_rgb)

        logging.info(f"Image saved as {image_path} and now displayed.")
        return image_path
    except Exception as e:
        logging.error(f"Failed to capture and display image: {e}")
        return None

# State handling functions
def handle_preview_state(disp, picam2, state, key_last_pressed_time, current_fps):
    show_live_preview(disp, picam2, f"Preview | FPS: {current_fps:.2f}")
    if check_key_pressed(disp, disp.GPIO_KEY1_PIN, key_last_pressed_time):
        state['current'] = State.CAPTURE
    elif check_key_pressed(disp, disp.GPIO_KEY3_PIN, key_last_pressed_time):
        state['current'] = State.VIEW_IMAGE
        state['image_index'] = display_latest_image(disp, state['save_dir'], "View Image")

def handle_view_image_state(disp, state, key_last_pressed_time):
    if check_key_pressed(disp, disp.GPIO_KEY2_PIN, key_last_pressed_time):
        state['current'] = State.PREVIEW
    elif check_key_pressed(disp, disp.GPIO_KEY_LEFT_PIN, key_last_pressed_time):
        if state['image_index'] is not None and state['image_index'] > 0:
            state['image_index'] -= 1
            image = cv2.imread(state['image_paths'][state['image_index']])
            display_image_with_state(disp, image, "View Image")
    elif check_key_pressed(disp, disp.GPIO_KEY_RIGHT_PIN, key_last_pressed_time):
        if state['image_index'] is not None and state['image_index'] < len(state['image_paths']) - 1:
            state['image_index'] += 1
            image = cv2.imread(state['image_paths'][state['image_index']])
            display_image_with_state(disp, image, "View Image")

def handle_capture_state(disp, picam2, capture_config, state):
    captured_image_path = capture_and_display_image(disp, picam2, capture_config, state['save_dir'], "Capture")
    state['image_paths'] = get_image_paths_sorted(state['save_dir'])
    state['image_index'] = len(state['image_paths']) - 1
    state['current'] = State.VIEW_IMAGE

# Main loop logic
def main_loop(disp, picam2, capture_config, save_dir):
    state = {
        'current': State.PREVIEW,
        'save_dir': save_dir,
        'image_paths': get_image_paths_sorted(save_dir),
        'image_index': None
    }
    key_last_pressed_time = initialize_key_state()

    target_fps = 24
    frame_time = 1.0 / target_fps
    fps_display_interval = 1.0  # Interval to update FPS display in seconds
    fps_counter = 0
    fps_timer_start = timer()
    current_fps = 0.0

    try:
        while True:
            start_time = timer()

            if state['current'] == State.PREVIEW:
                handle_preview_state(disp, picam2, state, key_last_pressed_time, current_fps)
            elif state['current'] == State.VIEW_IMAGE:
                handle_view_image_state(disp, state, key_last_pressed_time)
            elif state['current'] == State.CAPTURE:
                handle_capture_state(disp, picam2, capture_config, state)

            # FPS calculation
            fps_counter += 1
            elapsed_time = timer() - fps_timer_start
            if elapsed_time >= fps_display_interval:
                current_fps = fps_counter / elapsed_time
                # logging.info(f"Current FPS: {current_fps:.2f}")
                fps_counter = 0
                fps_timer_start = timer()

            # Control frame rate
            end_time = timer()
            elapsed_time = end_time - start_time
            sleep_time = max(0, frame_time - elapsed_time)
            time.sleep(sleep_time)
    except KeyboardInterrupt:
        logging.info("Program interrupted by user.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        picam2.close()
        disp.module_exit()
        logging.info("Program exited gracefully.")

# Main program entry point
if __name__ == "__main__":
    disp = initialize_display()
    if disp is not None:
        picam2, capture_config = initialize_camera()
        if picam2 is not None and capture_config is not None:
            save_dir = "/home/SeanPi-2w/camera/photo/"
            os.makedirs(save_dir, exist_ok=True)
            main_loop(disp, picam2, capture_config, save_dir)
        else:
            logging.error("Failed to initialize camera or capture configuration.")
    else:
        logging.error("Failed to initialize display.")
