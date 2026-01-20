import logging
import numpy as np
import cv2
from typing import List, Dict, Any, Optional
from ultralytics import YOLO
from src.core.base import BaseStage
from src.core.types import VideoFrame, Detection

logger = logging.getLogger(__name__)

class PPEClassifier(BaseStage):
    """
    Stage 3: Specialized PPE Classification (Unified Model).
    Uses Full Person Crops + YOLOv11 PPE Model.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        # Load Unified Model
        self.model_path = self.config.get("ppe_model_path", "runs/detect/models/training/ppe_yolo11n/weights/best.pt")
        self.device = self.config.get("device", "auto")
        
        self.model = None
        try:
            self.model = YOLO(self.model_path)
            logger.info(f"Loaded Unified PPE Detector: {self.model_path}")
            logger.info(f"Classes: {self.model.names}")
        except Exception as e:
            logger.warning(f"PPE Detector not found at {self.model_path}. Error: {e}")

    def process(self, frame: VideoFrame) -> VideoFrame:
        """
        Process frame: Crop Persons -> Unified Detect -> Map Logic.
        """
        if not frame.detections or not self.model:
            return frame
            
        # Get Person Tracks
        persons = [d for d in frame.detections if d.class_name == "person"]
        if not persons:
            return frame
            
        person_crops = []
        track_map = [] # (index) -> track_id
        
        img_h, img_w = frame.image.shape[:2]
        
        # 1. Prepare Crops (Full Person)
        for i, p in enumerate(persons):
            track_id = p.metadata.get("track_id")
            if track_id is None: continue
            
            bx1, by1, bx2, by2 = map(int, p.bbox)
            
            # Add Margin (10%)
            w = bx2 - bx1
            h = by2 - by1
            px = int(w * 0.1)
            py = int(h * 0.1)
            
            x1 = max(0, bx1 - px)
            y1 = max(0, by1 - py)
            x2 = min(img_w, bx2 + px)
            y2 = min(img_h, by2 + py)
            
            crop = frame.image[y1:y2, x1:x2]
            
            if crop.size > 0 and w > 20 and h > 50: # Minimum size check
                person_crops.append(crop)
                track_map.append({
                    "track_id": track_id,
                    "crop_origin": (x1, y1),
                    "bbox": p.bbox
                })
        
        if not person_crops:
            return frame

        # 2. Schema Map (Dataset Specific)
        # 0: helmet, 2: vest, 7: no_helmet
        # We want to map these to our internal "helmet", "vest", "no_helmet", "no_vest"
        
        new_detections = []
        
        # Batch Inference
        try:
            results = self.model(person_crops, verbose=False, conf=0.4) # Conf thresh 0.4
        except Exception as e:
            logger.error(f"PPE Batch Inference failed: {e}")
            return frame

        for i, res in enumerate(results):
            meta = track_map[i]
            track_id = meta["track_id"]
            origin_x, origin_y = meta["crop_origin"]
            
            # Check what we found in this person crop
            found_helmet = False
            found_vest = False
            found_no_helmet = False
            found_no_vest = False # If supported
            
            if hasattr(res, 'boxes') and res.boxes is not None:
                for box in res.boxes:
                    c_id = int(box.cls[0].item())
                    conf = float(box.conf[0].item())
                    label = res.names[c_id].lower()
                    
                    # Map to Global Coords
                    # box.xyxy is relative to crop
                    bx1, by1, bx2, by2 = box.xyxy[0].tolist()
                    gx1 = int(bx1 + origin_x)
                    gy1 = int(by1 + origin_y)
                    gx2 = int(bx2 + origin_x)
                    gy2 = int(by2 + origin_y)
                    
                    global_bbox = [gx1, gy1, gx2, gy2]
                    
                    det_class = None
                    mapping_conf = conf
                    
                    # Correct Logic Mapping with Thresholds
                    # Recommended by Senior Engineer
                    HELMET_THRESH = 0.65
                    VEST_THRESH = 0.60
                    NO_HELMET_THRESH = 0.75
                    NO_VEST_THRESH = 0.70

                    if "no_helmet" in label:
                        if conf >= NO_HELMET_THRESH:
                            det_class = "no_helmet"
                            found_no_helmet = True
                    elif "helmet" in label:
                        if conf >= HELMET_THRESH:
                            det_class = "helmet"
                            found_helmet = True
                    elif "no_vest" in label: 
                        if conf >= NO_VEST_THRESH:
                            det_class = "no_vest"
                            found_no_vest = True
                    elif "vest" in label:
                        if conf >= VEST_THRESH:
                            det_class = "vest"
                            found_vest = True
                        
                    if det_class:
                        new_detections.append(Detection(
                            class_id=0,
                            class_name=det_class,
                            confidence=conf,
                            bbox=global_bbox,
                            frame_number=frame.frame_number,
                            timestamp=frame.timestamp,
                            metadata={"track_id": track_id}
                        ))
            
            # 3. Handle Implicit Results (Unknown)
            # If nothing found for a category, we emit "unknown" explicitly 
            # OR we just emit nothing and let Rule Engine handle it (Wait, Rule Engine logic defaults to Unknown if no update).
            # But earlier we decided to emit "unknown" explicitly to prevent Stale State issues?
            # Actually, Rule Engine iterates `person_map` (detections for track).
            # If `helmet` found -> Present.
            # If `no_helmet` found -> Missing.
            # If neither found -> Unknown (Implicitly, logic handles it).
            # But the *previous* classifier explicitly emitted "unknown" to signal "We tried but failed".
            # Here, we "tried" (ran model on person). If model returns nothing, it's effectively "Unknown".
            
            # To be safe and compatible with my recent "Fix", I should explicitly emit "unknown" 
            # if we didn't find a definitive state for an item.
            
            # 3. Handle Implicit Results (Unknown)
            # If no PPE detections found for a category, we emit nothing.
            # The Rule Engine logic handles empty items list as "Unknown".
            if not found_helmet and not found_no_helmet:
                pass 
                
            if not found_vest and not found_no_vest:
                pass

        frame.detections.extend(new_detections)
        return frame
