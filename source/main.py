import json
import sys
from pathlib import Path

from vision.streamer import Streamer
from vision.tracker import Tracker
from vision.virtual_ptz import VirtualPTZ

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
    tracker = None
    virtual_ptz = None

    try:
        print("Initializing stream...")
        streamer_cfg = settings.get("streamer", {})
        streamer = Streamer(
            port=streamer_cfg.get("port", 10001),
            width=streamer_cfg.get("width", 1920),
            height=streamer_cfg.get("height", 1080),
            bitrate=streamer_cfg.get("bitrate", 1000000)
        )
        streamer.start()

        print("Initializing tracker...")
        tracker_cfg = settings.get("tracker", {})
        tracker = Tracker(
            model_path=tracker_cfg.get("model_path", "models/yolo11n.pt"),
            source=streamer.get_url(),
            conf_threshold=tracker_cfg.get("conf_threshold", 0.5)
        )
        results = tracker.start()

        print("Initializing virtual PTZ...")
        virtual_ptz_cfg = settings.get("virtual_ptz", {})
        virtual_ptz = VirtualPTZ(
            full_width=streamer_cfg.get("width", 1920),
            full_height=streamer_cfg.get("height", 1080),
            width=virtual_ptz_cfg.get("width", 640),
            height=virtual_ptz_cfg.get("height", 360),
            min_zoom=virtual_ptz_cfg.get("min_zoom", 1.0),
            max_zoom=virtual_ptz_cfg.get("max_zoom", 2.0)
        )

    except Exception as e:
        print(f"Startup failed: {e}")
        raise

    try:
        print("System running. Press Ctrl+C to stop")
        
        # Process tracker results
        for result in results:
            crop = virtual_ptz.get_crop_from_yolo_result(result)
            print(crop)

    except KeyboardInterrupt:
        print("\nStopping services...")

    finally:
        if streamer is not None:
            streamer.stop()
        print("Shutdown complete")
        sys.exit(0)

if __name__ == "__main__":
    main()