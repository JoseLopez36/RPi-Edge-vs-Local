# RPi-Virtual-PTZ

**A Distributed Virtual Tracking System with Visual Radar Feedback.**

This project implements a smart surveillance system using a Raspberry Pi 4 and a remote PC. The RPi streams video from the Camera Module v2, which is consumed by a remote PC running YOLOv11n for human detection (edge AI). The PC sends inference results to the RPi via MQTT, where PTZ calculations are performed. The RPi sends PTZ results back to the PC, which displays both the original video stream and the cropped PTZ view. The Sense HAT on the RPi serves as a "visual radar" to map targets and provides a physical interface to toggle focus between multiple subjects.

---

## 📋 Features

* **Distributed Edge AI:** YOLOv11n inference runs on a remote PC, offloading computation from the Raspberry Pi.
* **Virtual PTZ:** Simulates mechanical camera movement by digitally cropping and zooming into the Region of Interest (ROI) of the active target.
* **Multi-Target Tracking:** Detects multiple humans simultaneously using YOLOv11n on the remote PC.
* **MQTT Communication:** Real-time bidirectional communication between RPi and PC for inference results and PTZ commands.
* **Dual Video Display:** PC displays both the original 720p video stream and the cropped PTZ view simultaneously.
* **Visual Radar (Sense HAT):** Maps the relative position of detected targets onto the 8x8 LED Matrix (Red pixel = Active Target, White pixels = Other targets, Black pixels = Background).
* **Hardware Control:** Use the Sense HAT Joystick to cycle through detected people to change the PTZ focus target.
* **Low-Latency Streaming:** RPi streams 720p video over TCP (H.264) to the remote PC.

## 🛠️ Hardware & Requirements

### Raspberry Pi 4
* **Platform:** Raspberry Pi 4 Model B.
  * [Product Page](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/)
  * [Specifications](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/specifications/)
  * [Getting Started Guide](https://www.raspberrypi.com/documentation/computers/getting-started.html)
* **Sensor:** Raspberry Pi Camera Module v2.
  * [Product Page](https://www.raspberrypi.com/products/camera-module-v2/)
  * [Documentation](https://www.raspberrypi.com/documentation/accessories/camera.html)
  * [Examples](https://github.com/raspberrypi/picamera2/tree/main/examples)
* **I/O:** Raspberry Pi Sense HAT.
  * [Product Page](https://www.raspberrypi.com/products/sense-hat/)
  * [Documentation](https://www.raspberrypi.com/documentation/accessories/sense-hat.html)

### Remote PC (Edge AI)
* **Platform:** PC or laptop capable of running YOLOv11n inference in real-time.
* **Network:** Both RPi and PC must be on the same network for MQTT communication and video streaming.

### Software Stack
* **Raspberry Pi:**
  * Python 3.11.2
  * picamera2
  * MQTT client library (paho-mqtt)
* **Remote PC:**
  * Python 3.11.2
  * Ultralytics (YOLO)
  * MQTT client library (paho-mqtt)
  * OpenCV or similar for video display
  * [YOLO Documentation](https://docs.ultralytics.com/)

## 🚀 Installation

### Raspberry Pi Setup

1. **Clone the repository:**
```bash
git clone https://github.com/JoseLopez36/RPi-Virtual-PTZ.git
cd RPi-Virtual-PTZ
```

2. **Install system dependencies:**
```bash
sudo apt update
sudo apt install python3-picamera2
```

3. **Install Python requirements:**
```bash
pip install -r source/rpi/requirements.txt
```

### Remote PC Setup

1. **Clone the repository:**
```bash
git clone https://github.com/JoseLopez36/RPi-Virtual-PTZ.git
cd RPi-Virtual-PTZ
```

2. **Create and activate a virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Install Python requirements:**
```bash
pip install -r source/pc/requirements.txt
```

4. **Configure MQTT broker:** Ensure an MQTT broker is accessible on your network (e.g., Mosquitto). Update the broker address in `config/settings.json`.

## ⚙️ Configuration

The system uses `config/settings.json` for configuration. Edit this file to customize system parameters.

## 🎮 Usage

### System Architecture

1. **Raspberry Pi** streams 720p video from Camera Module v2 over TCP.
2. **Remote PC** receives the video stream and runs YOLOv11n inference to detect humans.
3. **PC** publishes inference results (bounding boxes, class IDs) to the RPi via MQTT.
4. **Raspberry Pi** receives inference results, calculates PTZ parameters based on the active target, and publishes PTZ commands back to the PC via MQTT.
5. **PC** displays both the original video stream and the cropped PTZ view.
6. **Raspberry Pi** displays target positions on the Sense HAT LED matrix and responds to joystick input to change the active target.

### Raspberry Pi

Run the main application on the Raspberry Pi:

```bash
python3 source/rpi/main.py
```

The RPi will:
- Stream 720p video over TCP (default port: 10001)
- Subscribe to MQTT topic for inference results
- Publish PTZ commands to MQTT
- Control target selection via Sense HAT joystick
- Display target map on Sense HAT LED matrix

### Remote PC

Run the edge AI application on the remote PC:

```bash
python3 source/pc/main.py
```

The PC will:
- Connect to the RPi video stream over TCP
- Run YOLOv11n inference on received frames
- Publish inference results to MQTT
- Subscribe to PTZ commands from MQTT
- Display original video and cropped PTZ view

### MQTT Topics

The system uses the following MQTT topics (configurable in `config/settings.json`):
- **Inference Results:** `rpi-ptz/inference` (PC → RPi)
- **PTZ Commands:** `rpi-ptz/ptz` (RPi → PC)

### Controls (Sense HAT Joystick)

| Input | Action |
| --- | --- |
| **Left / Right** | Cycle between detected targets. |
| **Middle Click** | Set PTZ to wide-angle view (no zoom). |
| **Up / Down** | Adjust digital zoom level. |