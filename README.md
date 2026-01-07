# RPi-Gimbal-Tracker

**Real-time Human Tracking System with Gimbal Control**

A Raspberry Pi-based system that captures video from a Siyi A8 Mini gimbal/camera, tracks humans using YOLO, automatically controls the gimbal to follow targets and streams annotated video to a PC.

## 📖 Project Overview

This project implements a closed-loop control system for automated gimbal tracking. The system:

1. **Captures** 1080p video from Siyi A8 Mini camera
2. **Detects & Tracks** humans using YOLOv8 on Raspberry Pi
3. **Controls** gimbal pan/tilt to automatically follow the target
4. **Streams** annotated video to PC for monitoring

## 🛠 Hardware Components

- **Embedded Device:** Raspberry Pi 4 Model B
- **Camera/Gimbal:** Siyi A8 Mini (1080p gimbal camera)
- **Display:** PC/Laptop for video monitoring

## ⚙️ Technologies

- **Object Detection:** YOLO11n
- **Tracking:** YOLO built-in tracker
- **Video Streaming:** GStreamer (H.264 encoding at 1080p@30fps)
- **Gimbal Control:** IP communication (Siyi protocol)
- **Network:** Ethernet for Gimbal-RPi communication, Wi-Fi for RPi-PC communication

## 🚀 Quick Start

### Prerequisites

- Raspberry Pi 4B with Raspberry Pi OS
- Siyi A8 Mini gimbal/camera
- PC with Linux/Windows (tested on Ubuntu 24.04)
- Wi-Fi connection between RPi and PC

### Setup

#### Raspberry Pi (Edge)

1. **Install System Dependencies:**
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3-pip python3-venv
   sudo apt-get install libgstreamer1.0-dev \
     libgstreamer-plugins-base1.0-dev \
     gstreamer1.0-plugins-good \
     gstreamer1.0-plugins-ugly \
     gstreamer1.0-plugins-bad \
     gstreamer1.0-tools
   ```

2. **Create and Run Virtual Environment:**
   ```bash
   cd scripts/rpi
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Python Dependencies:**
   ```bash
   TODO
   ```

4. **Run:**
   ```bash
   python3 main.py
   ```

#### PC (Server)

1. **Install System Dependencies:**
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3-pip python3-venv
   sudo apt-get install python3-gi python3-gi-cairo \
     gir1.2-gtk-3.0 libgirepository1.0-dev
   sudo apt-get install libgstreamer1.0-dev \
     libgstreamer-plugins-base1.0-dev \
     gstreamer1.0-plugins-good \
     gstreamer1.0-plugins-ugly \
     gstreamer1.0-plugins-bad \
     gstreamer1.0-tools \
     gstreamer1.0-libav
   ```

2. **Create and Run Virtual Environment:**
   ```bash
   cd scripts/pc
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Python Dependencies:**
   ```bash
   TODO
   ```

4. **Run:**
   ```bash
   python3 main.py
   ```