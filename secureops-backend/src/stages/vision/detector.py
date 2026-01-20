"""YOLO-based vision detector for PPE, machinery, and people."""

import cv2
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from ultralytics import YOLO
from src.core.base import BaseStage
from src.core.types import Detection, VideoFrame
from src.utils.yolo_utils import load_yolo_model, preprocess_frame, postprocess_detections
from src.core.exceptions import ModelLoadError, VideoProcessingError

logger = logging.getLogger(__name__)


class VisionDetector(BaseStage):
    """YOLO-based vision detector."""
    
    # COCO class IDs for construction site monitoring
    CLASS_PERSON = 0
    CLASS_BICYCLE = 1
    CLASS_CAR = 2
    CLASS_MOTORCYCLE = 3
    CLASS_AIRPLANE = 4
    CLASS_BUS = 5
    CLASS_TRAIN = 6
    CLASS_TRUCK = 7
    
    # Custom class mapping for construction
    CONSTRUCTION_CLASSES = {
        "person": CLASS_PERSON,
        "machinery": [CLASS_CAR, CLASS_BUS, CLASS_TRUCK],
        "vehicle": [CLASS_CAR, CLASS_BUS, CLASS_TRUCK, CLASS_MOTORCYCLE],
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.model_path = self.config.get("model_path", "models/yolov8n.pt")
        self.confidence_threshold = self.config.get("confidence_threshold", 0.25)
        self.device = self.config.get("device", "auto")
        self.classes = self.config.get("classes", [0, 2, 5])  # person, car, bus
        
        # Load model
        try:
            self.model = load_yolo_model(self.model_path, self.device)
            logger.info(f"Vision detector initialized with model {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            raise ModelLoadError(f"Failed to load YOLO model: {e}") from e
    
    def process(self, input_data: Any) -> Any:
        """Process video frame or frames."""
        if isinstance(input_data, VideoFrame):
            return self._process_frame(input_data)
        elif isinstance(input_data, list):
            return [self._process_frame(frame) for frame in input_data]
        elif isinstance(input_data, np.ndarray):
            # Single frame as numpy array
            frame = VideoFrame(
                frame_number=0,
                timestamp=datetime.now(),
                image=input_data
            )
            return self._process_frame(frame)
        else:
            raise ValueError(f"Unsupported input type: {type(input_data)}")
    
    def _process_frame(self, frame: VideoFrame) -> VideoFrame:
        """Process a single frame."""
        try:
            # Preprocess frame
            processed_image = preprocess_frame(frame.image)
            source_type = frame.metadata.get("source_type", "video")
            
            # Run YOLO inference
            if source_type == "video":
                # persist=True allows ID tracking across frames (crucial for video)
                results = self.model.track(
                    processed_image,
                    conf=self.confidence_threshold,
                    classes=self.classes,
                    persist=True,
                    tracker="bytetrack.yaml",
                    verbose=False
                )
            else:
                # For Images/PDFs: No tracking, independent detection
                results = self.model.predict(
                    processed_image,
                    conf=self.confidence_threshold,
                    classes=self.classes,
                    verbose=False
                )
            
            # Postprocess detections
            detection_data = postprocess_detections(
                results,
                frame.frame_number,
                class_names=self.model.names
            )
            
            # Convert to Detection objects
            detections = []
            for det_data in detection_data:
                tid = det_data.get("track_id")
                
                # Synthetic ID for non-video sources
                if tid is None and source_type != "video":
                    # Deterministic hash of bbox for this frame
                    # Ensures re-processing same image gives same IDs
                    bbox = det_data["bbox"] # [x1,y1,x2,y2]
                    # Create a simple hash from coordinates
                    # Multiplying to differentiate close coords
                    h_val = int(bbox[0]*1 + bbox[1]*100 + bbox[2]*10000 + bbox[3]*1000000) 
                    tid = abs(h_val) % 1000000
                
                detection = Detection(
                    class_id=det_data["class_id"],
                    class_name=det_data["class_name"],
                    confidence=det_data["confidence"],
                    bbox=det_data["bbox"],
                    frame_number=det_data["frame_number"],
                    timestamp=frame.timestamp,
                    metadata={"track_id": tid}
                )
                detections.append(detection)
            
            # Update frame with detections
            frame.detections = detections
            
            return frame
            
        except Exception as e:
            logger.error(f"Failed to process frame {frame.frame_number}: {e}")
            raise VideoProcessingError(f"Frame processing failed: {e}") from e
    
    def detect_ppe(self, frame: VideoFrame) -> List[Detection]:
        """Detect PPE (hard hat, vest) - placeholder for custom model."""
        # Note: YOLOv8n doesn't detect PPE by default
        # This would require a custom trained model
        # For now, return empty list or use person detections as proxy
        return [d for d in frame.detections if d.class_name == "person"]
    
    def detect_machinery(self, frame: VideoFrame) -> List[Detection]:
        """Detect construction machinery."""
        machinery_classes = ["car", "bus", "truck"]
        return [
            d for d in frame.detections
            if d.class_name.lower() in machinery_classes
        ]
    
    def detect_people(self, frame: VideoFrame) -> List[Detection]:
        """Detect people."""
        return [d for d in frame.detections if d.class_name == "person"]

