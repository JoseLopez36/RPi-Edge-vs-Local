import time
import sys
import os

# Add project root to sys.path to ensure imports work if run from root
sys.path.append(os.getcwd())

from utils import load_config
from mqtt_client import MQTTClient
from camera_stream import CameraStream
from ptz_logic import PTZController
from sense_hat_interface import SenseHatInterface

def main():
    print("Starting RPi Virtual PTZ system...")
    
    config = load_config()
    if not config:
        return

    # Initialize components
    mqtt = MQTTClient(config)
    camera = CameraStream(config)
    ptz = PTZController(config)
    sense_hat = SenseHatInterface()

    def on_mqtt_message(topic, payload):
        if topic == config['mqtt']['topics']['inference']:
            # Process inference results
            detections = payload.get('detections', [])
            ptz_cmd = ptz.update(detections)
            mqtt.publish_ptz(ptz_cmd)
            sense_hat.update_display(detections, ptz.target_id)

    mqtt.set_callback(on_mqtt_message)

    try:
        mqtt.start()
        camera.start()
        
        while True:
            # Main loop tasks (e.g., check joystick)
            # event = sense_hat.get_joystick_event()
            # if event:
            #     ptz.handle_input(event)
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        mqtt.stop()
        camera.stop()

if __name__ == "__main__":
    main()
