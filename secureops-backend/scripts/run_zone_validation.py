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
DATA_DIR = Path("data")
FRAMES_DIR = DATA_DIR / "frames"
ZONES_DIR = DATA_DIR / "zones"
OVERLAYS_DIR = DATA_DIR / "overlays" / "runtime"
POLYGONS_FILE = ZONES_DIR / "polygons.yaml"
LABELS_CSV = ZONES_DIR / "labels.csv"

MODELS = {
    "person": Path("yolov8n.pt"),
    "machinery": Path("machinery_best.pt")
}

FPS = 2.0

def load_polygons():
    if not POLYGONS_FILE.exists():
        return {}
    with open(POLYGONS_FILE, 'r') as f:
        return yaml.safe_load(f)

def load_gt_labels():
    if not LABELS_CSV.exists():
        return {}
    gt = {}
    with open(LABELS_CSV, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # key: frame_id + object_idx (since ID might not be stable if re-running detection?)
            # Wait, auto-label and verification are separate runs. 
            # If we run detection AGAIN, Track IDs might drift if not deterministic.
            # But YOLO prediction on images is usually deterministic if seed set.
            # Ideally we'd save the detections in auto-label and reuse them. 
            # But the prompt says "Feed detections to ZoneMonitor" implying re-detection or passing through.
            # I will key GT by frame_id and naive index for comparison stats, 
            # OR just comparing aggregate counts.
            fid = row["frame_id"]
            if fid not in gt: gt[fid] = []
            gt[fid].append(row)
    return gt

def main():
    if OVERLAYS_DIR.exists():
        shutil.rmtree(OVERLAYS_DIR)
    OVERLAYS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Init
    monitor = ZoneMonitor()
    poly_map = load_polygons()
    gt_map = load_gt_labels()
    
    # Models
    logger.info("Loading models...")
    models = {}
    for k, v in MODELS.items():
        if v.exists():
            models[k] = YOLO(str(v))
            
    # Sorted Frames
    frame_ids = sorted(poly_map.keys())
    
    total_gt_violations = 0
    total_runtime_violations = 0
    
    # Replay
    logger.info(f"Replaying {len(frame_ids)} frames at {FPS} FPS...")
    
    current_video = None
    frame_idx_in_video = 0
    
    for frame_id in frame_ids:
        # Determine Video Context (for timestamp calculation)
        # frame_id = "video_name/frame_xxxxx.jpg"
        parts = frame_id.split("/")
        video_name = parts[0]
        
        if video_name != current_video:
            current_video = video_name
            frame_idx_in_video = 0
            # Reset Monitor State on new video
            monitor.state.clear()
            
            # Load Zones for this video (from first frame of video)
            # The poly_map contains per-frame list, we take the first one
            zones_def = poly_map[frame_id]
            # Convert to dict for Monitor
            z_dict = {}
            for z in zones_def:
                z_dict[z["zone_id"]] = Polygon(z["polygon"])
            monitor.set_zones(z_dict)
        
        # Calculate Timestamp
        timestamp = frame_idx_in_video * (1.0 / FPS)
        frame_idx_in_video += 1
        
        # Load Image
        img_path = FRAMES_DIR / frame_id
        img = cv2.imread(str(img_path))
        if img is None: continue
        
        # Detections (Re-run)
        detections = []
        if "person" in models:
            res = models["person"].predict(img, verbose=False, classes=[0])[0]
            for box in res.boxes:
                 detections.append({
                    "track_id": int(box.id[0]) if box.id is not None else -1, # Tracker needed?
                    # Since we are running on independent frames without a ByteTrack wrapper here,
                    # ID will be None or unstable unless we force tracking.
                    # YOLO().track() is better but for "Extract Frames" dataset, 
                    # we often treat them as independent unless we simulate a video stream.
                    # The prompt says: "Track (object_id, zone_id)".
                    # IF IDs are missing, ZoneMonitor logic (state tracking) fails.
                    # I MUST use model.track() or assign IDs. 
                    # Given "Replay frames sequentially", model.track() is appropriate.
                    # However, model.track() usually expects a video source or persistent tracker.
                    # On individual images, we need `persist=True`.
                    
                    "label": "person", 
                    "bbox": box.xyxy[0].cpu().numpy(),
                    "conf": float(box.conf[0])
                })

        # Wait, standard predict() doesn't track. I need tracking for temporal logic.
        # I will use model.track(img, persist=True)
        
        # Clearing detections for correct implementation
        detections = []
        
        # We need separate tracking for person/machine or mixed? 
        # YOLO only runs one model at a time usually unless merged. 
        # I will prioritize MACHINERY model then PERSON model, 
        # but running two trackers in parallel on same image sequence is tricky (IDs might clash).
        # For this verification, I will stick to "predict" and Mock IDs if tracking isn't easy, 
        # BUT `ZoneMonitor` strictly depends on IDs.
        # I will attempt `model.track(img, persist=True)` for ONE model (Person) for simplicity 
        # unless I merge them. 
        # Let's run just PERSON tracking for now as it's most common, or try both.
        # Actually, if I use `persist=True`, I need to call it sequentially.
        
        # Let's do:
        # 1. Person Tracking
        res_p = models["person"].track(img, persist=True, verbose=False, classes=[0])[0]
        for box in res_p.boxes:
            if box.id is not None:
                detections.append({
                    "track_id": int(box.id[0]),
                    "label": "person",
                    "bbox": box.xyxy[0].cpu().numpy()
                })
                
        # 2. Machinery Tracking (Independent tracker instance?)
        # YOLOv8 track() handles its own state.
        res_m = models["machinery"].track(img, persist=True, verbose=False)[0]
        names_m = models["machinery"].names
        for box in res_m.boxes:
             if box.id is not None:
                # Add offset to machinery IDs to avoid collision with person IDs
                detections.append({
                    "track_id": int(box.id[0]) + 1000, 
                    "label": names_m[int(box.cls[0])],
                    "bbox": box.xyxy[0].cpu().numpy()
                })

        # Run Monitor
        violations = monitor.check_violations(detections, timestamp=timestamp)
        
        # Stats
        # GT Violations (for this frame)
        gt_rows = gt_map.get(frame_id, [])
        gt_in_zone_count = sum(1 for r in gt_rows if r["in_zone"] == "true")
        
        total_gt_violations += gt_in_zone_count
        total_runtime_violations += len(violations)
        
        # Draw Results
        # Zones
        for z in poly_map[frame_id]:
             pts = np.array(z["polygon"], np.int32).reshape((-1, 1, 2))
             cv2.polylines(img, [pts], True, (255, 0, 0), 2) # Blue
             
        # Violations (RED)
        v_ids = {v.object_id for v in violations}
        
        for det in detections:
            x1, y1, x2, y2 = map(int, det["bbox"])
            tid = det["track_id"]
            
            if tid in v_ids:
                color = (0, 0, 255) # Red
                label = f"VIOLATION {tid}"
            else:
                color = (0, 255, 0) # Green
                label = f"SAFE {tid}"
                
            cv2.rectangle(img, (x1,y1), (x2,y2), color, 2)
            cv2.putText(img, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
        # Save
        out_path = OVERLAYS_DIR / frame_id
        out_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(out_path), img)

    logger.info("=== Validation Results ===")
    logger.info(f"Total Spatial Violations (GT): {total_gt_violations}")
    logger.info(f"Total Runtime Violations (Temporal): {total_runtime_violations}")
    if total_runtime_violations < total_gt_violations:
        logger.info("Note: Runtime count is lower as expected due to 1.0s temporal smoothing.")
    elif total_runtime_violations > total_gt_violations:
        logger.warning("Runtime > GT? Check logic.")
    else:
        logger.info("Counts match exactly (Rare for temporal logic).")

if __name__ == "__main__":
    main()
