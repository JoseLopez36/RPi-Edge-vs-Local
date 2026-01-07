import time
import sys
from video_streamer import VideoStreamer

# Configuration
MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC = "/control/action"
PC_HOST = "192.168.2.28" # Replace with PC IP
PC_PORT = 5000

def on_control_message(payload):
    """Callback when a message is received from MQTT"""
    print(f"Control message received: {payload}")
    # TODO: Parse payload and trigger GPIO action
    # gpio_handler.perform_action(payload)

def main():
    print("RPi Edge Node Started")
    
    # Initialize Modules
    mqtt_sub = MQTTSubscriber(MQTT_BROKER, MQTT_TOPIC, on_control_message)
    streamer = VideoStreamer()
    gpio = GPIOHandler()
    
    try:
        # Start Services
        mqtt_sub.start()
        streamer.start_stream(PC_HOST, PC_PORT)
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("Stopping services...")
        mqtt_sub.stop()
        streamer.stop_stream()
        gpio.cleanup()
        sys.exit(0)

if __name__ == "__main__":
    main()

