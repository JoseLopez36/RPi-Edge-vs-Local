import json
import sys
import time
from pathlib import Path
import matplotlib.pyplot as plt

from vision.streamer import Streamer
from vision.tracker import Tracker
# from vision.ptz import PTZPipeline
# from hardware.display import VisualRadar
# from hardware.buttons import JoystickController
# from hardware import sensors

def load_settings():
    root = Path(__file__).resolve().parents[1]
    settings_path = root / "config" / "settings.json"
    try:
        raw = settings_path.read_text().strip()
        if not raw:
            return {}
        return json.loads(raw)
    except Exception as e:
        print(f"Warning: failed to load settings.json: {e}")
        return {}

def main():
    print("RPi Virtual PTZ started")

    settings = load_settings()

    streamer = None
    # tracker = None
    # radar = None
    # joystick = None
    # pipeline = None

    try:
        print("Initializing stream...")
        stream_cfg = settings.get("stream", {})
        streamer = Streamer(
            port=stream_cfg.get("port", 10001),
            width=stream_cfg.get("width", 1920),
            height=stream_cfg.get("height", 1080),
            bitrate=stream_cfg.get("bitrate", 1000000)
        )
        streamer.start()

        print("Initializing tracker...")
        tracker_cfg = settings.get("tracker", {})
        tracker = Tracker(
            model_path=tracker_cfg.get("model_path", "models/yolo11n.pt"),
            source=streamer.get_url(),
            conf_threshold=tracker_cfg.get("conf_threshold", 0.5)
        )
        tracker_results = tracker.start()

        # sense_cfg = settings.get("sense_hat", {})
        # radar = VisualRadar(enabled=sense_cfg.get("enabled", True))
        # joystick = JoystickController(enabled=sense_cfg.get("enabled", True))

        # pipeline = PTZPipeline(
        #     camera=streamer,
        #     tracker=tracker,
        #     streamer=streamer,
        #     display=radar,
        #     joystick=joystick,
        #     sensors=sensors,
        #     config=settings,
        # )
    except Exception as e:
        print(f"Startup failed: {e}")
        return

    try:
        print("Collecting tracker data (100 frames)... Press Ctrl+C to stop early")
        frame_numbers = []
        detection_counts = []
        
        for frame_num, result in enumerate(tracker_results):
            if frame_num >= 100:  # Collect 100 frames
                break
            
            targets = tracker.results_to_target_list(result)
            frame_numbers.append(frame_num)
            detection_counts.append(len(targets))
            
            if frame_num % 10 == 0:
                print(f"Frame {frame_num}: {len(targets)} detections")
        
        # Plot results
        print(f"\nPlotting results for {len(frame_numbers)} frames...")
        plt.figure(figsize=(10, 6))
        plt.plot(frame_numbers, detection_counts, 'b-', marker='o', markersize=4)
        plt.xlabel('Frame Number')
        plt.ylabel('Number of Tracked Objects')
        plt.title('Tracker Results - Detections per Frame')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()
        
        print("Plot displayed. System will continue running...")
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping services...")
    finally:
        if streamer is not None:
            streamer.stop()
        print("Shutdown complete")
        sys.exit(0)

if __name__ == "__main__":
    main()