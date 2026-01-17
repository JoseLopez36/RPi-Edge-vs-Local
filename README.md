# RPi-Virtual-PTZ

**An Embedded Virtual Tracking System with Visual Radar Feedback.**

This project implements a smart surveillance system on a Raspberry Pi 4. It uses Computer Vision to detect humans and performs **Virtual Pan-Tilt-Zoom (e-PTZ)** by dynamically cropping the high-resolution camera stream. The Sense HAT is utilized as a "Visual Radar" to map targets and provides a physical interface to toggle focus between multiple subjects.

---

## 📋 Features

* **Virtual PTZ:** Simulates mechanical camera movement by digitally cropping and zooming into the Region of Interest (ROI) of the active target.
* **Multi-Target Tracking:** Detects multiple humans simultaneously using YOLO.
* **Visual Radar (Sense HAT):** Maps the relative position of detected targets onto the 8x8 LED Matrix (Red pixel = Active Target, White pixels = Other targets, Black pixels = Background).
* **Hardware Control:** Use the Sense HAT Joystick to cycle through detected people to change the PTZ focus target.
* **Low-Latency Streaming:** Outputs the processed, stabilized video stream via GStreamer (RTSP/UDP).

## 🛠️ Hardware & Requirements

* **Platform:** Raspberry Pi 4 Model B.
  * [Product Page](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/)
  * [Specifications](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/specifications/)
  * [Getting Started Guide](https://www.raspberrypi.com/documentation/computers/getting-started.html)
* **Sensor:** Raspberry Pi Camera Module v2.
  * [Product Page](https://www.raspberrypi.com/products/camera-module-v2/)
  * [Documentation](https://www.raspberrypi.com/documentation/accessories/camera.html)
* **I/O:** Raspberry Pi Sense HAT.
* **Software Stack:**
* Python 3.12+
* GStreamer
* Ultralytics (YOLO)
  * [YOLO on Raspberry Pi Guide](https://docs.ultralytics.com/guides/raspberry-pi/#flash-raspberry-pi-os-to-raspberry-pi)

## ⚙️ Architecture

The system operates in three concurrent stages:

1. **Acquisition:** Captures wide-angle video via `libcamerasrc`.
2. **Processing:**
* Detect bounding boxes of humans.
* Map coordinates to the LED matrix.
* Listen for Joystick events to select the `target_id`.
3. **Output:**
* `videocrop`: Adjusts the view based on the selected target's centroid.
* `textoverlay`: displaying telemetry (Temp/FPS).

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
sudo apt install python3-opencv gstreamer1.0-tools libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev sense-hat
```

3. **Install Python requirements:**
```bash
pip install -r requirements.txt
```

### Web Viewer Setup

The video stream from the Raspberry Pi can be viewed through a web browser. Once the main application is running on the Raspberry Pi, access the stream at:

```
http://<RPi_IP_ADDRESS>:8000
```

For example: `http://192.168.1.112:8000`

## ⚙️ Configuration

The system uses `config/settings.json` for configuration. Edit this file to customize system parameters

## 🎮 Usage

### Raspberry Pi

Run the main application on the Raspberry Pi:

```bash
python3 source/rpi/main.py
```

### Web Viewer

Access the video stream from any device with a web browser by navigating to:

```
http://<RPi_IP_ADDRESS>:8000
```

For example: `http://192.168.1.112:8000`

### Controls (Sense HAT Joystick)

| Input | Action |
| --- | --- |
| **Left / Right** | Cycle between detected targets. |
| **Middle Click** | Set PTZ to wide-angle view (no zoom). |
| **Up / Down** | Adjust digital zoom level. |