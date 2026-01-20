import cv2
import numpy as np
from pathlib import Path
import uuid
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class FrameAnnotator:
    """Utility to annotate and save frames with violation evidence."""
    
    def __init__(self, base_dir: str = "storage/violations"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
    def save_violation_frame(
        self, 
        frame: np.ndarray, 
        detections: List[Dict[str, Any]], 
        upload_id: str, 
        violation_type: str,
        filename_prefix: str = "violation"
    ) -> Optional[str]:
        """
        Draws bounding boxes/labels on frame and saves it.
        Returns the relative path string (e.g., 'violations/uuid/ppe/frame.jpg').
        
        Args:
            frame: Numpy array (RGB or BGR).
            detections: List of dicts with 'bbox', 'class_name', 'confidence', etc.
                        Only include relevant detections (e.g., the violator).
            upload_id: ID of the video upload.
            violation_type: Subfolder name (ppe, proximity, zone).
            filename_prefix: Prefix for the file name.
        """
        if frame is None or frame.size == 0:
            logger.warning("Empty frame provided for annotation.")
            return None
            
        try:
            # Copy frame to avoid modifying original pipeline frame
            # Ensure BGR for OpenCV
            if len(frame.shape) == 3 and frame.shape[2] == 3:
                # Assuming input might be RGB (from video loader), convert to BGR for saving
                # If pipeline passes RGB, we switch to BGR. Standard cv2 is BGR.
                # Pipeline usually carries RGB.
                annotated = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            else:
                annotated = frame.copy()

            # Draw detections (Strictly per passed list - Orchestrator filters Safe people)
            for det in detections:
                bbox = det.get("bbox")
                if bbox:
                    x1, y1, x2, y2 = [int(c) for c in bbox]
                    
                    # Draw Box (Red for violation)
                    cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    
                    # Construct Precise Label per User Spec
                    # "Missing Helmet", "Missing Vest", "Missing Helmet & Vest"
                    missing = det.get("missing_items", [])
                    label_text = "Violation"
                    
                    if missing:
                        # Capitalize items: helmet -> Helmet
                        items = [m.capitalize() for m in missing]
                        label_text = f"Missing {' & '.join(items)}"
                    elif det.get("class_name"):
                        label_text = det.get("class_name") # Fallback for non-PPE
                        
                    # Text Background for readability
                    (tw, th), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                    
                    # Ensure label doesn't go off-screen top
                    text_y = y1 - 10
                    if text_y < 20: 
                        text_y = y1 + 25 # Move inside box if at top edge
                        
                    # Background Box
                    cv2.rectangle(annotated, (x1, text_y - th - 5), (x1 + tw, text_y + 5), (0, 0, 255), -1)
                    
                    # White Text
                    cv2.putText(annotated, label_text, (x1, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Additional visual cues for Proximity/Zone could be added here
            # e.g. drawing lines or polygons passed in 'detections' or separate args
            # For now, generic bbox support is sufficient.

            # Prepare Output Path
            # storage/violations/{upload_id}/{violation_type}/
            out_dir = self.base_dir / upload_id / violation_type
            out_dir.mkdir(parents=True, exist_ok=True)
            
            # Filename: unique ID to avoid overwrites
            filename = f"{filename_prefix}_{uuid.uuid4().hex[:8]}.jpg"
            out_path = out_dir / filename
            
            # Save
            success = cv2.imwrite(str(out_path), annotated)
            if success:
                # Return relative path for DB/API (e.g. violations/123/ppe/img.jpg)
                # We strip 'storage/' from the start if we want strictly relative to storage root
                # or relative to serving root. 
                # Let's return path relative to 'storage' so generic media server can find it.
                # If base_dir is "storage/violations", resolving relative to "storage"
                
                # Assumption: API mounts 'storage' dir to '/media'
                # So we want path starting 'violations/...'
                try:
                    rel_path = out_path.relative_to(self.base_dir.parent)
                    return str(rel_path)
                except ValueError:
                    return str(out_path)
            else:
                logger.error(f"Failed to write image to {out_path}")
                return None
                
        except Exception as e:
            logger.error(f"Error saving violation frame: {e}")
            return None
