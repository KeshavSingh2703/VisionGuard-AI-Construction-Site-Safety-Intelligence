"""YOLO utility functions."""

import cv2
import numpy as np
from typing import Tuple, Optional
from ultralytics import YOLO
import logging

logger = logging.getLogger(__name__)


def load_yolo_model(model_path: str, device: str = "auto") -> YOLO:
    """Load YOLO model. Auto-downloads if file doesn't exist or is empty."""
    from pathlib import Path
    
    model_file = Path(model_path)
    
    # Check if file exists and has content
    if not model_file.exists() or model_file.stat().st_size == 0:
        logger.info(f"Model file {model_path} not found or empty. Auto-downloading...")
        # Extract model name (e.g., "yolov8n.pt" from "models/yolov8n.pt")
        model_name = model_file.name
        # YOLO will auto-download if we pass just the name
        model_path = model_name
    
    try:
        # YOLO will auto-download the model if it doesn't exist locally
        model = YOLO(model_path)
        
        # If auto-downloaded, save to the specified path
        if model_file.exists() and model_file.stat().st_size == 0:
            # Model was downloaded to default location, copy it
            from shutil import copy2
            default_model_path = Path.home() / ".ultralytics" / "weights" / model_name
            if default_model_path.exists():
                copy2(default_model_path, model_file)
                logger.info(f"Saved downloaded model to {model_file}")
        
        # Set device
        if device == "auto":
            device = "cuda" if hasattr(model, 'device') and model.device.type == "cuda" else "cpu"
        
        logger.info(f"YOLO model loaded from {model_path} on {device}")
        return model
    except Exception as e:
        logger.error(f"Failed to load YOLO model: {e}")
        raise


def preprocess_frame(frame: np.ndarray) -> np.ndarray:
    """Preprocess frame for YOLO."""
    if frame is None or frame.size == 0:
        raise ValueError("Invalid frame")
    
    # Ensure RGB format
    if len(frame.shape) == 3 and frame.shape[2] == 3:
        # Assume BGR from OpenCV, convert to RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    return frame


def postprocess_detections(results, frame_number: int, class_names: Optional[dict] = None) -> list:
    """Postprocess YOLO detection results."""
    detections = []
    
    if results is None or len(results) == 0:
        return detections
    
    # Get first result (YOLO returns list)
    result = results[0]
    
    if result.boxes is None:
        return detections
    
    boxes = result.boxes
    class_names_map = class_names or result.names
    
    for i in range(len(boxes)):
        box = boxes[i]
        
        # Get detection details
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])
        class_name = class_names_map.get(class_id, f"class_{class_id}")
        
        # Get bounding box coordinates
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
        
        # Extract Track ID (if available from model.track())
        track_id = None
        if box.id is not None:
            track_id = int(box.id[0])
        else:
            # Deterministic Fallback for single-frame/stateless detections
            # Use frame_number * 100 + detection_index to ensure uniqueness/stability within frame
            # But stability across frames is NOT guaranteed without tracker.
            # This allows PPERuleEngine to at least process "snapshot" logic.
            track_id = (frame_number * 1000) + i

        detections.append({
            "class_id": class_id,
            "class_name": class_name,
            "confidence": confidence,
            "bbox": (float(x1), float(y1), float(x2), float(y2)),
            "frame_number": frame_number,
            "track_id": track_id
        })
    
    return detections

