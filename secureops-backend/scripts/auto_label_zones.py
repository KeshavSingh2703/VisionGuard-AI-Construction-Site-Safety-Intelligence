import yaml
import logging
import csv
import cv2
import numpy as np
import shutil
from pathlib import Path
from shapely.geometry import Point, Polygon
from ultralytics import YOLO

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Config
DATA_DIR = Path("data")
FRAMES_DIR = DATA_DIR / "frames"
ZONES_DIR = DATA_DIR / "zones"
OVERLAYS_DIR = DATA_DIR / "overlays" / "auto_labels"
POLYGONS_FILE = ZONES_DIR / "polygons.yaml"
OUTPUT_CSV = ZONES_DIR / "labels.csv"

MODELS = {
    "person": Path("yolov8n.pt"),
    "machinery": Path("machinery_best.pt")
}

def load_polygons():
    if not POLYGONS_FILE.exists():
        return {}
    with open(POLYGONS_FILE, 'r') as f:
        return yaml.safe_load(f)

def get_centroid(box):
    x1, y1, x2, y2 = box
    return (x1 + x2) / 2, (y1 + y2) / 2

def main():
    if OVERLAYS_DIR.exists():
        shutil.rmtree(OVERLAYS_DIR)
    OVERLAYS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load
    poly_map = load_polygons()
    if not poly_map:
        logger.error("No polygons found.")
        return

    logger.info("Loading models...")
    models = {}
    for k, v in MODELS.items():
        if v.exists():
            models[k] = YOLO(str(v))
        else:
            logger.warning(f"Model {k} not found.")

    if not models:
        logger.error("No models loaded.")
        return

    # CSV
    f_csv = open(OUTPUT_CSV, 'w', newline='')
    writer = csv.writer(f_csv)
    writer.writerow(["frame_id", "object_id", "object_type", "in_zone"])
    
    # Process Frames
    # We iterate through the polygon map keys to find frames
    sorted_frame_ids = sorted(poly_map.keys())
    
    logger.info(f"Processing {len(sorted_frame_ids)} frames...")
    
    for frame_id in sorted_frame_ids:
        # Construct absolute path
        # frame_id is relative like "video_name/frame_00001.jpg"
        img_path = FRAMES_DIR / frame_id
        
        if not img_path.exists():
            logger.warning(f"Image {img_path} missing.")
            continue
            
        img = cv2.imread(str(img_path))
        if img is None: continue
        
        # Get Zones
        zones = poly_map[frame_id]
        
        # Detections
        detections = []
        if "person" in models:
            res = models["person"].predict(img, verbose=False, classes=[0])[0]
            for box in res.boxes:
                 detections.append({
                    "cls": "person", 
                    "bbox": box.xyxy[0].cpu().numpy(),
                    "id": box.id[0] if box.id is not None else -1 
                })
        
        if "machinery" in models:
            res = models["machinery"].predict(img, verbose=False)[0]
            names = models["machinery"].names
            for box in res.boxes:
                cls_id = int(box.cls[0])
                detections.append({
                    "cls": names[cls_id],
                    "bbox": box.xyxy[0].cpu().numpy(),
                    "id": box.id[0] if box.id is not None else -1
                })
                
        # Check Containment
        for i, det in enumerate(detections):
            x1, y1, x2, y2 = map(int, det["bbox"])
            cx, cy = get_centroid((x1,y1,x2,y2))
            point = Point(cx, cy)
            
            in_any_zone = False
            
            for z in zones:
                # Shape
                poly_pts = z["polygon"]
                poly = Polygon(poly_pts)
                
                # Check (Point.within)
                if poly.contains(point): # Auto-label strict containment
                    in_any_zone = True
                    # Draw Polygon
                    pts = np.array(poly_pts, np.int32).reshape((-1, 1, 2))
                    cv2.polylines(img, [pts], True, (0, 0, 255), 2)
                    break
                else:
                    # Draw Green Poly
                    pts = np.array(poly_pts, np.int32).reshape((-1, 1, 2))
                    cv2.polylines(img, [pts], True, (0, 255, 0), 2)

            writer.writerow([frame_id, i, det["cls"], str(in_any_zone).lower()])
            
            # Annotate
            color = (0, 0, 255) if in_any_zone else (0, 255, 0)
            cv2.rectangle(img, (x1,y1), (x2,y2), color, 2)
            cv2.circle(img, (int(cx), int(cy)), 4, color, -1)
            
        # Save Overlay
        # Mirror directory structure
        out_path = OVERLAYS_DIR / frame_id
        out_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(out_path), img)

    f_csv.close()
    logger.info(f"Done. Labels at {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
