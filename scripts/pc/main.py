"""
PC Server Node - Main Entry Point

This module receives and displays the annotated video stream from the Raspberry Pi.
"""

import time
import sys
import queue
import cv2
from video_receiver import VideoReceiver

# Configuration
LISTEN_PORT = 5000

# Frame queue for video display
frame_queue = queue.Queue(maxsize=10)


def on_frame_received(frame):
    """Callback when a video frame is received"""
    if not frame_queue.full():
        frame_queue.put(frame)


def main():
    print("PC Server Node Started")
    print("Waiting for video stream from Raspberry Pi...")
    
    # Initialize video receiver
    receiver = VideoReceiver(on_frame_received)
    
    try:
        # Start receiving video stream
        print(f"Starting video receiver on port {LISTEN_PORT}...")
        receiver.start_receiving(LISTEN_PORT)
        
        # Display video frames
        print("Video stream active. Press 'q' to quit.")
        while True:
            if not frame_queue.empty():
                frame = frame_queue.get()
                
                # Display frame
                cv2.imshow("RPi Gimbal Tracker - Annotated Video", frame)
                
                # Check for exit key
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("Quitting...")
                    break
            else:
                # Sleep briefly to reduce CPU usage when no frames
                time.sleep(0.001)
            
    except KeyboardInterrupt:
        print("\nStopping services...")
    finally:
        receiver.stop_receiving()
        cv2.destroyAllWindows()
        print("Shutdown complete.")
        sys.exit(0)


if __name__ == "__main__":
    main()
