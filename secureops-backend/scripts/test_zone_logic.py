import yaml
import logging
import csv
import cv2
import numpy as np
import shutil
from pathlib import Path
from shapely.geometry import Polygon
from ultralytics import YOLO
from src.stages.vision.zone_monitor import ZoneMonitor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Config
DATASET_DIR = Path("dataset/restricted_zones")
IMAGES_DIR = DATASET_DIR / "images"
POLYGONS_FILE = DATASET_DIR / "polygons.yaml"
DEBUG_DIR = DATASET_DIR / "verify_overlays"

MODELS = {
    "person": Path("yolov8n.pt"),
    "machinery": Path("machinery_best.pt")
}

def load_polygons():
    """Load the validation dataset polygons."""
    with open(POLYGONS_FILE, 'r') as f:
        return yaml.safe_load(f)

def main():
    if DEBUG_DIR.exists():
        shutil.rmtree(DEBUG_DIR)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Initialize Monitor
    monitor = ZoneMonitor()
    # Note: Monitor expects load_zones logic, but our validation dataset has per-image zones.
    # We will manually inject zones per frame for this verification.
    
    # 2. Load Data & Models
    poly_map = load_polygons()
    
    logger.info("Loading models...")
    models = {}
    for k, v in MODELS.items():
        if v.exists():
            models[k] = YOLO(str(v))
    
    images = list(IMAGES_DIR.glob("*.jpg")) + list(IMAGES_DIR.glob("*.png"))
    logger.info(f"Processing {len(images)} images...")
    
    total_violations = 0
    total_safe = 0
    
    for img_path in images:
        filename = img_path.name
        img = cv2.imread(str(img_path))
        if img is None: continue
        
        # Get Per-Image Zone
        zone_info = poly_map.get(filename)
        if not zone_info: continue
            
        points = zone_info["points"]
        zone_poly = Polygon(points)
        zone_id = zone_info["name"]
        
        # Inject into Monitor (Simulating that this camera has this zone)
        monitor.zones = {zone_id: zone_poly}
        
        # Detections
        detections = []
        
        # Person
        if "person" in models:
            res = models["person"].predict(img, verbose=False, classes=[0])[0]
            for box in res.boxes:
                detections.append({
                    "track_id": 100 + int(box.id[0]) if box.id is not None else -1, # Mock ID
                    "label": "person", 
                    "bbox": box.xyxy[0].cpu().numpy()
                })
        
        # Machinery
        if "machinery" in models:
            res = models["machinery"].predict(img, verbose=False)[0]
            names = models["machinery"].names
            for box in res.boxes:
                cls_id = int(box.cls[0])
                detections.append({
                    "track_id": 200 + int(box.id[0]) if box.id is not None else -1, # Mock ID
                    "label": names[cls_id],
                    "bbox": box.xyxy[0].cpu().numpy()
                })
        
        # Run Logic
        # NOTE: To trigger temporal smoothing, we simulate:
        # 1. t=0 input (Enters state)
        # 2. t=1.1 input (Triggers violation)
        # Since these are static images, we will call check_violations twice.
        
        # T=0
        monitor.check_violations(detections, timestamp=1000.0)
        
        # T=1.1 (Same detections)
        violations = monitor.check_violations(detections, timestamp=1001.1)
        
        # Visualization
        has_violation = len(violations) > 0
        total_violations += len(violations)
        total_safe += (len(detections) - len(violations))
        
        # Draw Poly
        pts = np.array(points, np.int32).reshape((-1, 1, 2))
        cv2.polylines(img, [pts], True, (0, 255, 255), 3)
        
        # Draw Detections
        violation_ids = {v.object_id for v in violations}
        
        for det in detections:
            x1, y1, x2, y2 = map(int, det["bbox"])
            obj_id = det["track_id"]
            
            if obj_id in violation_ids:
                color = (0, 0, 255) # Red
                status = "VIOLATION"
            else:
                color = (0, 255, 0)
                status = "SAFE"
                
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            cv2.putText(img, f"{det['label']} {status}", (x1, y1-10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Save
        cv2.imwrite(str(DEBUG_DIR / filename), img)
        
        # Clear state for next image (Simulate new camera)
        monitor.state.clear() 

    logger.info(f"Verification Complete.")
    logger.info(f"Total Violations Detected: {total_violations}")
    logger.info(f"Total Safe Objects: {total_safe}")
    logger.info(f"Output saved to {DEBUG_DIR}")

if __name__ == "__main__":
    main()
