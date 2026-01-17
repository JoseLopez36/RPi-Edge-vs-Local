"""
YOLO Human Detection and Tracking Module

This module uses YOLO11n for human detection and YOLO's built-in tracker
for tracking detected humans across frames
"""

import os
from ultralytics import YOLO

class Tracker:
    def __init__(self, model_path, source, conf_threshold=0.5):
        self.model_path = model_path
        self.source = source
        self.conf_threshold = conf_threshold
        self._model = None
        print(f"Initializing YOLO Tracker (model: {model_path})")
        self._load_model()
    
    def _load_model(self):
        """Load YOLO model"""
        try:
            # Resolve model path relative to project root
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(script_dir))
            model_full_path = os.path.join(project_root, self.model_path)
            
            if not os.path.exists(model_full_path):
                raise FileNotFoundError(f"Model file not found: {model_full_path}")
            
            self._model = YOLO(model_full_path)
            print(f"YOLO model loaded successfully from {model_full_path}")
        except Exception as e:
            print(f"Error loading YOLO model: {e}")
            raise
    
    def start(self):
        """
        Detect humans and track them across frames

        Returns:
            List of tracked objects with bounding boxes and IDs
            Each object contains: id, bbox (x1, y1, x2, y2), confidence, class
        """
        if self._model is None:
            raise ValueError("YOLO model not loaded")
        
        # Run YOLO detection with tracking
        # Class 0 in COCO dataset is 'person'
        results = self._model.track(
            self.source,
            conf=self.conf_threshold,
            classes=[0],
            stream=True
        )
        
        return results

    def results_to_target_list(self, results):
        """
        Convert a single Ultralytics 'results' object into a list of target dicts

        Each dict contains: id, bbox (x1,y1,x2,y2), confidence, class
        """
        target_list = []
        if results is None:
            return target_list

        boxes = getattr(results, "boxes", None)
        if boxes is None:
            return target_list

        for b in boxes:
            # xyxy: tensor([[x1, y1, x2, y2]])
            xyxy = getattr(b, "xyxy", None)
            if xyxy is None:
                continue
            try:
                bbox = xyxy.squeeze().tolist()
            except Exception:
                # Fallback: best-effort conversion
                bbox = list(xyxy[0])

            conf = getattr(b, "conf", None)
            try:
                confidence = float(conf.item()) if conf is not None else 0.0
            except Exception:
                confidence = float(conf) if conf is not None else 0.0

            cls = getattr(b, "cls", None)
            try:
                class_id = int(cls.item()) if cls is not None else -1
            except Exception:
                class_id = int(cls) if cls is not None else -1

            track_id = getattr(b, "id", None)
            if track_id is not None:
                try:
                    track_id = int(track_id.item())
                except Exception:
                    try:
                        track_id = int(track_id)
                    except Exception:
                        track_id = None

            target_list.append(
                {
                    "id": track_id,
                    "bbox": bbox,
                    "confidence": confidence,
                    "class": class_id,
                }
            )

        return target_list