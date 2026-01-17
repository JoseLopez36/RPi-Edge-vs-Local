import json
import sys
from pathlib import Path

from vision.streamer import Streamer
from vision.tracker import Tracker
# from vision.ptz import PTZPipeline
# from hardware.display import VisualRadar
# from hardware.buttons import JoystickController
# from hardware import sensors

def load_settings():
    root = Path(__file__).resolve().parents[2]
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
    print("RPi Virtual PTZ Started")

    settings = load_settings()

    streamer = None
    tracker = None
    # radar = None
    # joystick = None
    # pipeline = None

    try:
        print("Initializing stream...")
        stream_cfg = settings.get("stream", {})
        streamer = Streamer(
            width=stream_cfg.get("width", 1920),
            height=stream_cfg.get("height", 1080),
            framerate=stream_cfg.get("framerate", 30),
            port=stream_cfg.get("port", 8000)
        )
        streamer.start()

        print("Initializing tracker...")
        tracker_cfg = settings.get("tracker", {})
        tracker = Tracker(
            model_path=tracker_cfg.get("model_path", "models/yolo11n.pt"),
            source=streamer.get_local_stream_url(),
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

    try:
        print("System running. Press Ctrl+C to stop")
    except KeyboardInterrupt:
        print("\nStopping services...")
    finally:
        if streamer is not None:
            streamer.stop()
        print("Shutdown complete")
        sys.exit(0)

if __name__ == "__main__":
    main()