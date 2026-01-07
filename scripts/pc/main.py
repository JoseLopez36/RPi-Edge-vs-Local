import time
import sys
import queue
import os

import cv2
from video_receiver import VideoReceiver
from model_inference import ModelInference
from mqtt_publisher import MQTTPublisher

# Configuration
MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC = "/control/action"
LISTEN_PORT = 5000
MODEL_PATH = "models/my_model.tflite"

# Frame queue
frame_queue = queue.Queue(maxsize=10)

def on_frame_received(frame):
    """Callback when a video frame is received"""
    if not frame_queue.full():
        frame_queue.put(frame)

def main():
    print("PC Server Node Started")
    
    global inference_engine, mqtt_pub
    
    # Initialize Modules
    print("Initializing Inference Engine...")
    inference_engine = ModelInference(MODEL_PATH)
    inference_engine.load_model()
    
    print("Connecting to MQTT Broker...")
    mqtt_pub = MQTTPublisher(MQTT_BROKER, MQTT_TOPIC)
    mqtt_pub.connect()
    
    receiver = VideoReceiver(on_frame_received)
    
    try:
        # Start Receiver
        print(f"Starting Video Receiver on port {LISTEN_PORT}...")
        receiver.start_receiving(LISTEN_PORT)
        
        # Keep main thread alive and handle display
        print("Press 'q' to quit video stream")
        while True:
            if not frame_queue.empty():
                frame = frame_queue.get()
                
                # TODO: Run Inference
                # result = inference_engine.predict(frame)
                
                # Display Frame
                cv2.imshow("RPi Video Stream", frame)
                
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
        mqtt_pub.stop()
        cv2.destroyAllWindows()
        sys.exit(0)

if __name__ == "__main__":
    main()

