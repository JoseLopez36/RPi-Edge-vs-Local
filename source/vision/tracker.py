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
        """Detect humans and track them across frames"""
        if self._model is None:
            raise ValueError("YOLO model not loaded")
        
        # Run YOLO detection with tracking
        # Class 0 in COCO dataset is 'person'
        results = self._model.track(
            self.source,
            conf=self.conf_threshold,
            classes=[0],
            stream=True,
            imgsz=640,
            persist=True
        )
        
        return results