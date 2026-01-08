"""
YOLO Human Detection and Tracking Module

This module uses YOLO11n for human detection and YOLO's built-in tracker
for tracking detected humans across frames.
"""

import os
from ultralytics import YOLO

class YoloTracker:
    def __init__(self, model_path="models/yolo11n.pt", conf_threshold=0.5):
        """
        Initialize YOLO tracker
        
        Args:
            model_path: Path to YOLO11n model weights
            conf_threshold: Confidence threshold for detections (0.0, 1.0)
        """
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self.model = None
        self.tracker = None
        print(f"Initializing YOLO Tracker (model: {model_path})")
        self.load_model()
    
    def load_model(self):
        """Load YOLO model"""
        try:
            # Resolve model path relative to project root
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(script_dir))
            model_full_path = os.path.join(project_root, self.model_path)
            
            if not os.path.exists(model_full_path):
                raise FileNotFoundError(f"Model file not found: {model_full_path}")
            
            self.model = YOLO(model_full_path)
            print(f"YOLO model loaded successfully from {model_full_path}")
        except Exception as e:
            print(f"Error loading YOLO model: {e}")
            raise
    
    def track(self, frame):
        """
        Detect humans and track them across frames
        
        Args:
            frame: Input frame as numpy array (BGR format)
            
        Returns:
            List of tracked objects with bounding boxes and IDs
            Each object contains: id, bbox (x1, y1, x2, y2), confidence, class
        """
        if self.model is None:
            return []
        
        # Run YOLO detection with tracking
        # Class 0 in COCO dataset is 'person'
        results = self.model.track(
            frame,
            conf=self.conf_threshold,
            classes=[0],  # Only detect humans (person class)
            persist=True,
            verbose=False
        )
        
        tracked_objects = []
        
        if results[0].boxes is not None and results[0].boxes.id is not None:
            boxes = results[0].boxes
            for i in range(len(boxes)):
                # Get bounding box coordinates
                bbox = boxes.xyxy[i].cpu().numpy()  # [x1, y1, x2, y2]
                track_id = int(boxes.id[i].cpu().numpy())
                confidence = float(boxes.conf[i].cpu().numpy())
                
                tracked_objects.append({
                    'id': track_id,
                    'bbox': bbox,
                    'confidence': confidence,
                    'class': 'person'
                })
        
        return tracked_objects
    
    def get_primary_target(self, tracked_objects, frame_center=None):
        """
        Select primary target to track (e.g., largest or closest to center)
        
        Args:
            tracked_objects: List of tracked objects from detect_and_track
            frame_center: Tuple (x, y) of frame center (optional)
            
        Returns:
            Primary target object or None
        """
        if not tracked_objects:
            return None
        
        # Simple strategy: select largest bounding box (most prominent person)
        # TODO: Could implement more sophisticated selection (closest to center, etc.)
        largest_area = 0
        primary_target = None
        
        for obj in tracked_objects:
            bbox = obj['bbox']
            area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
            if area > largest_area:
                largest_area = area
                primary_target = obj
        
        return primary_target
    
    def calculate_gimbal_command(self, target, frame_width, frame_height):
        """
        Calculate gimbal pan/tilt commands based on target position
        
        Args:
            target: Target object with bbox
            frame_width: Frame width in pixels
            frame_height: Frame height in pixels
            
        Returns:
            Tuple (pan_offset, tilt_offset) in degrees
            Positive pan = right, positive tilt = up
        """
        if target is None:
            return (0.0, 0.0)
        
        # Get bounding box coordinates
        bbox = target['bbox']

        # Calculate center of bounding box
        target_center_x = (bbox[0] + bbox[2]) / 2
        target_center_y = (bbox[1] + bbox[3]) / 2
        
        # Calculate offset from frame center
        frame_center_x = frame_width / 2
        frame_center_y = frame_height / 2
        
        offset_x = target_center_x - frame_center_x
        offset_y = target_center_y - frame_center_y
        
        # Convert pixel offset to angular offset (degrees)
        pan_offset = (offset_x / frame_width) * 60.0  # degrees
        tilt_offset = -(offset_y / frame_height) * 45.0  # degrees (negative for up)
        
        return (pan_offset, tilt_offset)