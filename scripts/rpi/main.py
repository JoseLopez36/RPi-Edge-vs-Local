"""
Raspberry Pi - Main Entry Point

This module orchestrates:
1. Human detection and tracking using YOLO11n
2. Gimbal control to follow targets
3. Annotated video streaming to PC
"""

import time
import sys
from yolo_tracker import YoloTracker
from gimbal_controller import GimbalController
from video_streamer import VideoStreamer

# Configuration
GIMBAL_IP = "192.168.144.25"  # Replace with Siyi A8 Mini IP
PC_HOST = "192.168.2.28"  # Replace with PC IP
PC_PORT = 5000
MODEL_PATH = "models/yolo11n.pt"  # Path to YOLO11n model (relative to project root)

def main():
    print("RPi Gimbal Tracker Started")
    
    # Initialize Modules
    print("Initializing YOLO tracker...")
    tracker = YoloTracker(model_path=MODEL_PATH, conf_threshold=0.5)
    
    print("Initializing gimbal controller...")
    gimbal = GimbalController(gimbal_ip=GIMBAL_IP)
    gimbal.connect()
    
    print("Initializing video streamer...")
    streamer = VideoStreamer()
    
    try:
        # TODO: Main logic

        # Keep main thread alive
        print("System running. Press Ctrl+C to stop")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping services...")

    finally:
        streamer.stop_stream()
        gimbal.disconnect()
        print("Shutdown complete")
        sys.exit(0)

if __name__ == "__main__":
    main()