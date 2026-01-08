"""
Setup YOLO model to be NCNN (optimized for embedded platforms)
"""

from ultralytics import YOLO

# Load a YOLO11n PyTorch model
model = YOLO("models/yolo11n.pt")

# Export the model to NCNN format
model.export(format="ncnn")  # creates 'yolo11n_ncnn_model'