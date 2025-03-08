# Raspberry Pi Zero 2 Camera

[中文版本](README_zh.md)

This project provides all the files and information needed to build a **compact, portable Raspberry Pi Zero 2 camera**.

If you encounter any problems in usage, design, or programming, or if you have any suggestions for improvements, feel free to [open an Issue](../../issues) to discuss with us!

---

### Brief Features

- **Ultra-compact form factor**: Built around the Raspberry Pi Zero 2, making it easy to carry and deploy.
- **Auto-focus**: Utilizes the Raspberry Pi Camera Module 3 with AutoFocus support to capture sharper images.
- **Display and power integration**: Combines the Waveshare 1.3inch LCD HAT and Waveshare 1.3inch UPS HAT for a complete shooting experience.
- **Customizable, flexible expansion**: Raspberry Pi supports various camera modules and has a large open-source community, offering many interchangeable parts and 3D printing designs.

---

### Demo

**Finished Product / Camera Appearance**

![Demo Image](https://github.com/SeanLo940076/RaspberryPi-0-2W-Camera/blob/main/Demo/Camera1.jpg)
![Demo Image](https://github.com/SeanLo940076/RaspberryPi-0-2W-Camera/blob/main/Demo/Camera2.jpg)

**Sample Photos - Click to view original images**

[![Demo Image 1](https://github.com/SeanLo940076/RaspberryPi-0-2W-Camera/blob/main/Demo/Photo1_thumbnail.jpg)](https://github.com/SeanLo940076/RaspberryPi-0-2W-Camera/blob/main/Demo/Photo1.jpg)
[![Demo Image 2](https://github.com/SeanLo940076/RaspberryPi-0-2W-Camera/blob/main/Demo/Photo2_thumbnail.jpg)](https://github.com/SeanLo940076/RaspberryPi-0-2W-Camera/blob/main/Demo/Photo2.jpg)

---

### Hardware Setup

1. **Hardware**:  
   - [Raspberry Pi Zero 2](https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/)
   - [Raspberry Pi Camera Module 3](https://www.raspberrypi.com/products/camera-module-3/)
   - [Waveshare 1.3inch LCD HAT](https://www.waveshare.com/wiki/1.3inch_LCD_HAT)
   - [Waveshare 1.3inch UPS HAT](https://www.waveshare.com/wiki/UPS_HAT_(C))
   - [3D-printed camera adapter board](https://github.com/SeanLo940076/Raspberry-Pi-Zero-2-Camera/blob/main/3D%20Print/camera%20adapter%20board.stl) — a component to secure the camera. A simple design is included in this project for printing and fitting the Camera Module 3.
   - microSD

2. **Operating System**:  
   - Recommended **Raspberry Pi Lite OS**

---

### Assembly Steps

1. **Stack the LCD HAT**  
   - First, stack the **Waveshare 1.3inch LCD HAT** onto the **Pi Zero 2**, ensuring the 40-pin headers align correctly. Secure it with M2.5 screws in the four corners.

2. **Connect the flat cable**  
   - Use the included FFC cable to connect the camera interface on the **Pi Zero 2**.

3. **Stack the UPS HAT**  
   - Stack the **Waveshare 1.3inch UPS HAT** onto the **Pi Zero 2**, making sure the power pins align correctly. Secure it again with M2.5 screws in the four corners.
   - Note: It may be easier to thread the **FFC Cable** through the **UPS HAT** first before connecting it to the camera.

4. **Mount the Camera Module**  
   - Attach the **Camera Module 3** to the 3D-printed camera adapter board using M2 screws.

5. **Secure the camera adapter board**  
   - Stack the **camera adapter board** onto the back of the **UPS HAT** and secure it with M2.5 screws in the four corners.

6. **Power test**  
   - Connect a battery to the **UPS HAT** to charge.  
   - Confirm that the **Pi Zero 2** boots up properly and the LCD displays an image.

> **Tip**: Since this design is still under continuous improvement, if you find that the dimensions or hole placements are off, feel free to adjust the 3D model yourself.

---

### Installation / Usage Example

Below is an example based on **Raspberry Pi Lite OS**, demonstrating basic installation and shooting operations:

> You might see a message like “× This environment is externally managed” during installation. In that case, just proceed with:
   ```bash
   sudo apt install python3-requests
   ```

1. **Update the system and enable features**
   ```bash
   sudo apt update
   sudo apt upgrade -y
   sudo raspi-config
   ```
   - In `Interface Options`, enable **Camera**, **SPI**, **I2C**.

2. **Change the swap size**  
   In `/etc/dphys-swapfile`, find `CONF_SWAPSIZE` and change it to 512:
   ```bash
   sudo nano /etc/dphys-swapfile
   CONF_SWAPSIZE=512
   ```
   Then reboot.

3. **Install dependencies for the LCD HAT**
   ```bash
   wget https://github.com/joan2937/lg/archive/master.zip
   unzip master.zip
   cd lg-master
   sudo make install
   ```

   Then edit:
   ```bash
   sudo nano /boot/firmware/config.txt
   gpio=6,19,5,26,13,21,20,16=pu
   ```

4. **Install dependencies for the UPS HAT**
   ```bash
   sudo apt-get install p7zip
   wget https://files.waveshare.com/upload/4/40/UPS_HAT_C.7z
   7zr x UPS_HAT_C.7z -r -o./
   cd UPS_HAT_C
   python3 INA219.py
   ```

5. **Install OpenCV**
   ```bash
   sudo apt install python3-opencv-python
   ```

6. **Sync photos to a computer via Samba**
   ```bash
   sudo apt update
   sudo apt install samba
   sudo systemctl enable smbd
   sudo systemctl start smbd
   ```
   (Configuration for Samba can be organized later.)

7. **Run the camera software**
   ```bash
   python3 main.py
   ```

8. **Set up auto-start on boot**
   Edit the `rc.local` file:
   ```bash
   sudo nano /etc/rc.local
   ```

   > Switch to the specified user so that the script runs in the user's environment.
   > When running as root, the working directory and environment variables are different (e.g., the default path might be /root),
   > which can cause the script to fail in locating resources like the photo storage directory.
   
   Add the following line before `exit 0`, resulting in:
   > Replace “User” with your actual username
   ```bash

   su - User -c "/usr/bin/python3 /User/SeanPi-2w/Raspberry-Pi-Zero-2-Camera/Camera_v2/main.py &"
   exit 0
   ```

9. **Camera button guide**
   - KEY1 takes a photo
   - Left button opens the photo gallery
   - In the gallery, use left/right buttons to scroll through photos

---

### Features

**Current Functions**
1. **Auto-focus shooting**  
2. **Photo gallery**  
3. **Sync photos to computer**  
4. **Battery level estimation**  
5. **Program can auto-start on boot**

**Upcoming Updates**
- [ ] **Restart program button**
- [X] **Exit program button**
- [X] **Photo gallery error detection**
- [ ] **Auto-focus animation**
- [ ] **Improve battery level estimation**
- [X] **Adjust interaction mode**
- [ ] **Add joystick model and button model**
- [ ] **Optimize network connection**
- [ ] **Video recording**
- [X] **Add on-screen FPS calculation**

---

### License

This project is licensed under the MIT License. For more details, please refer to the [LICENSE](LICENSE) file.  
Thank you for reading, enjoy using this project, and we look forward to your feedback and contributions!