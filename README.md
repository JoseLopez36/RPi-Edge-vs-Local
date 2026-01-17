# RPi-Virtual-PTZ

**An Embedded Virtual Tracking System with Visual Radar Feedback.**

This project implements a smart surveillance system on a Raspberry Pi 4. It uses YOLOv11n to detect humans and performs **Virtual Pan-Tilt-Zoom** by dynamically cropping the high-resolution camera stream. The Sense HAT is utilized as a "visual radar" to map targets and provides a physical interface to toggle focus between multiple subjects.

---

## 📋 Features

* **Virtual PTZ:** Simulates mechanical camera movement by digitally cropping and zooming into the Region of Interest (ROI) of the active target.
* **Multi-Target Tracking:** Detects multiple humans simultaneously using YOLOv11n.
* **Visual Radar (Sense HAT):** Maps the relative position of detected targets onto the 8x8 LED Matrix (Red pixel = Active Target, White pixels = Other targets, Black pixels = Background).
* **Hardware Control:** Use the Sense HAT Joystick to cycle through detected people to change the PTZ focus target.
* **Low-Latency Streaming:** Outputs the processed, stabilized video stream over TCP (H.264).

## 🛠️ Hardware & Requirements

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
* **Software Stack:**
* Python 3.11.2
* Ultralytics (YOLO)
  * [YOLO on Raspberry Pi Guide](https://docs.ultralytics.com/guides/raspberry-pi/#flash-raspberry-pi-os-to-raspberry-pi)

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
pip install -r requirements.txt
```

## ⚙️ Configuration

The system uses `config/settings.json` for configuration. Edit this file to customize system parameters.

## 🎮 Usage

### Raspberry Pi

Run the main application on the Raspberry Pi:

```bash
python3 source/main.py
```

### Stream Client

The stream is served as raw H.264 over TCP. Connect from a client on the same
network to the Raspberry Pi on port `10001`.

Example with `ffplay`:

```bash
ffplay -f h264 -fflags nobuffer -flags low_delay -probesize 32 -analyzeduration 0 -framedrop -sync video tcp://raspberrypi.local:10001
```

### Controls (Sense HAT Joystick)

| Input | Action |
| --- | --- |
| **Left / Right** | Cycle between detected targets. |
| **Middle Click** | Set PTZ to wide-angle view (no zoom). |
| **Up / Down** | Adjust digital zoom level. |