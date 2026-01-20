import logging
import numpy as np
from typing import List, Dict, Any, Optional
from ultralytics import YOLO
from src.core.base import BaseStage
from src.core.types import VideoFrame, Detection

logger = logging.getLogger(__name__)

import torch

class PoseEstimator(BaseStage):
    """
    Stage 2: Pose Estimation for specialized cropping.
    Extracts keypoints for detected persons to define robust Head/Torso ROIs.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.model_path = self.config.get("model_path", "yolov8n-pose.pt")
        
        # Device auto-detection
        requested_device = self.config.get("device", "auto")
        if requested_device == "auto":
            if torch.backends.mps.is_available():
                self.device = "mps"
            elif torch.cuda.is_available():
                self.device = "cuda"
            else:
                self.device = "cpu"
        else:
            self.device = requested_device
            
        self.conf_threshold = self.config.get("min_confidence", 0.25)
        
        try:
            self.model = YOLO(self.model_path)
            logger.info(f"PoseEstimator initialized with {self.model_path} on {self.device}")
        except Exception as e:
            logger.error(f"Failed to load Pose model: {e}")
            raise

    def process(self, frame: VideoFrame) -> VideoFrame:
        """
        Run pose estimation.
        Enhances existing Person detections with 'keypoints' metadata if matched,
        or we can just run independent pose inference.
        
        Strategy: Run pose on full frame (optimized), map to existing Tracks.
        """
        if not frame.detections:
            logger.debug("Pose: No detections in frame.")
            return frame
            
        # Only needed if there are people
        person_tracks = [d for d in frame.detections if d.class_name == "person"]
        if not person_tracks:
            logger.debug(f"Pose: No person tracks found (Found: {[d.class_name for d in frame.detections]})")
            return frame
            
        logger.debug(f"Pose: Found {len(person_tracks)} persons. Running inference...")
            
        try:
            results = self.model(frame.image, conf=self.conf_threshold, verbose=False, device=self.device)
            
            # Map pose results to tracks based on IOU
            # Result objects contain boxes and keypoints
            if not results:
                logger.debug("Pose: Inference returned no results.")
                return frame
                
            res = results[0]
            if not res.boxes or not res.keypoints:
                logger.debug(f"Pose: Results empty. Boxes={res.boxes is not None}, Keypoints={res.keypoints is not None}")
                return frame
                
            # Naive matching: Find pose-box that overlaps most with track-box
            # In production, ByteTrack + Pose is often one step, but we are chaining.
            
            pose_boxes = res.boxes.xyxy.cpu().numpy()
            keypoints = res.keypoints.data.cpu().numpy() # (N, 17, 3) usually (x,y,conf)
            logger.debug(f"PoseEstimator: Found {len(pose_boxes)} pose-persons. Tracks: {len(person_tracks)}")

            for t_idx, track_det in enumerate(person_tracks):
                tx1, ty1, tx2, ty2 = track_det.bbox
                best_iou = 0
                best_idx = -1
                
                track_area = (tx2 - tx1) * (ty2 - ty1)
                
                for i, pbox in enumerate(pose_boxes):
                    px1, py1, px2, py2 = pbox
                    
                    # IOU calc
                    ix1 = max(tx1, px1)
                    iy1 = max(ty1, py1)
                    ix2 = min(tx2, px2)
                    iy2 = min(ty2, py2)
                    
                    if ix2 > ix1 and iy2 > iy1:
                        inter = (ix2 - ix1) * (iy2 - iy1)
                        pose_area = (px2 - px1) * (py2 - py1)
                        union = track_area + pose_area - inter
                        iou = inter / union if union > 0 else 0
                        
                        if iou > best_iou:
                            best_iou = iou
                            best_idx = i
                            
                if best_idx != -1 and best_iou > 0.3: # Relaxed threshold
                    # Found match, attach keypoints
                    track_det.metadata["keypoints"] = keypoints[best_idx]
                    logger.debug(f"Pose: Matched Track {track_det.metadata.get('track_id')} with Pose {best_idx} (IoU={best_iou:.2f})")
                else:
                    logger.debug(f"Pose: No match for Track {track_det.metadata.get('track_id')} (Max IoU={best_iou:.2f})")
                    
        except Exception as e:
            logger.warning(f"Pose estimation failed: {e}")
            
        return frame
