
# Raspberry Pi Zero 2 Camera

此專案提供了構建**緊湊型便攜式 Raspberry Pi Zero 2 相機**所需的所有檔案和資訊。

如果在使用、設計或程式上遇到任何問題，或有任何改進建議，歡迎提出 [Issue](../../issues) 與我們討論！

---

### 簡要特色 (Features)

- **超小體積**：以 Raspberry Pi Zero 2 為核心，方便攜帶與應用。
- **自動對焦**：採用 Raspberry Pi Camera Module 3，支援 AutoFocus 功能，可取得更清晰的影像。
- **顯示與供電整合**：支援 Waveshare 1.3inch LCD HAT 與 Waveshare 1.3inch UPS HAT，實現完整拍攝體驗。
- **可客製化、擴充彈性**：Raspberry Pi 可搭配多種 Camera 模組，並擁有龐大的開源社區，有許多替換或升級零組件與 3D 列印設計可搭配使用。
---

### 硬體配置
1. **硬體**：
   - Raspberry Pi Zero 2
   - Raspberry Pi Camera Module 3
   - Waveshare 1.3inch LCD HAT
   - Waveshare 1.3inch UPS HAT
   - microSD
   - 3D 列印相機轉接板 － 需要一個能將相機固定的轉接板；此專案內含簡易設計，可供列印並適配 Camera Module 3。

2. **作業系統**：
   - 建議 **Raspberry Pi Lite OS**

---

### 組裝步驟 (Assembly Steps)

1. **疊加 LCD HAT**
   - 先將 **Waveshare 1.3inch LCD HAT** 與 Raspberry Pi Zero 2 疊合，確保 40-pin 接腳對應正確，並在四角鎖上 M2.5 螺絲。  
2. **連接排線**  
   - 使用隨附的扁平排線 (FFC Cable) 將 Raspberry Pi Zero 2 的相機介面連接。
3. **疊加 UPS HAT**  
   - 將 **Waveshare 1.3inch UPS HAT** 與 Raspberry Pi Zero 2 疊合，確保供電接角對應正確，並在四角鎖上 M2.5 螺絲。
   - 注意：FFC Cable 可以先穿過 UPS HAT 模組，之後會比較好連線到相機。
4. **固定 Camera Module**
   - 將 Camera Module 3 固定在 3D 相機轉接板上， 這邊使用的是 M2 螺絲。
5. **固定相機轉接板** 
   - 將 **相機轉接板** 疊合至 UPS HAT 模組背後，並在四角鎖上 M2.5 螺絲。
5. **電源測試**  
   - 接上電池到 UPS HAT 充電。  
   - 確認 Pi Zero 2 能正常啟動並且螢幕有顯示畫面。

> **提示**：由於此設計仍在持續改良中，若遇到尺寸不合或孔位不相符，可以自行微調 3D 模型。

---

### 安裝 / 使用範例 (Installation / Usage Examples)

以下以 **Raspberry Pi Lite OS** 為例，示範基礎安裝與拍攝操作：

1. **更新系統並啟用 Camera**
   ```bash
   sudo apt update
   sudo apt upgrade -y
   sudo raspi-config
   ```
   - 在 `Interface Options` 中啟用 **Camera**，然後重新開機。

2. **後續待更新**

---

### Demo

**成品展示 / 外觀照片**

![Demo Image](https://github.com/SeanLo940076/RaspberryPi-0-2W-Camera/blob/main/Demo/Camera1.jpg)
![Demo Image](https://github.com/SeanLo940076/RaspberryPi-0-2W-Camera/blob/main/Demo/Camera2.jpg)

**拍攝範例結果**

[![Demo Image 1](https://github.com/SeanLo940076/RaspberryPi-0-2W-Camera/blob/main/Demo/Photo1_thumbnail.jpg)](https://github.com/SeanLo940076/RaspberryPi-0-2W-Camera/blob/main/Demo/Photo1.jpg)
[![Demo Image 2](https://github.com/SeanLo940076/RaspberryPi-0-2W-Camera/blob/main/Demo/Photo2_thumbnail.jpg)](https://github.com/SeanLo940076/RaspberryPi-0-2W-Camera/blob/main/Demo/Photo2.jpg)

---

### 功能實現

**目前已有功能**
1. **自動對焦拍攝**
2. **相簿功能**
3. **照片上傳功能**
4. **電池電量估計**

**未來預計更新**

- [ ] **縮圖生成問題**
- [ ] **對焦時的動畫**
- [ ] **優化電池電量估計**
- [ ] **調整功能互動模式**
- [ ] **增加蘑菇頭模型與按鈕模型**
- [ ] **優化網路連線方式**
- [ ] **錄影功能**

---

### License

本專案採用 MIT License 授權。詳細內容請參考 [LICENSE](LICENSE) 檔案。
感謝你的閱讀，祝你使用愉快，期待你的回饋與貢獻！
```
