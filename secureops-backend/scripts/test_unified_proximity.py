import os
import shutil
import random
import logging
import time
import math
from pathlib import Path
from ultralytics import YOLO
import cv2
import numpy as np
from src.stages.vision.proximity import ProximityDetector

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
MACHINERY_MODEL_PATH = Path("machinery_best.pt")
PERSON_MODEL_PATH = Path("yolov8n.pt")
VAL_IMAGES_DIR = Path("machinery_dataset/images/val")
OUTPUT_DIR = Path("proximity_test_output")

def get_center(bbox):
    x1, y1, x2, y2 = bbox
    return (int((x1 + x2) / 2), int((y1 + y2) / 2))

def main():
    if not MACHINERY_MODEL_PATH.exists():
        logger.error(f"Machinery model not found at {MACHINERY_MODEL_PATH}")
        return

    # Setup output
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load Models
    logger.info("Loading models...")
    machinery_model = YOLO(str(MACHINERY_MODEL_PATH))
    person_model = YOLO(str(PERSON_MODEL_PATH))

    # Initialize Logic
    detector = ProximityDetector()

    # Pick Images
    # We want images that likely have both people and machinery if possible.
    # But since we have pure machinery validation set, we might not have people.
    # So we might need to rely on the fact that OpenImages 'Truck' images might have people.
    # miniexcav might have operators.
    # Or we just test on the machinery images and hope for the best, 
    # OR we use the previous 'unified' test images? 
    # Let's check 'unified_test/output_images' inputs? 
    # No, let's stick to the machinery validation set for now, checking 10 randoms.
    # Or better: Use the 5 images from before + 5 more.
    
    all_images = list(VAL_IMAGES_DIR.glob("*.jpg")) + list(VAL_IMAGES_DIR.glob("*.png"))
    selected_images = random.sample(all_images, min(10, len(all_images)))
    logger.info(f"Selected {len(selected_images)} images.")

    for i, img_path in enumerate(selected_images):
        logger.info(f"Processing {img_path.name}...")
        
        # Read Image
        img = cv2.imread(str(img_path))
        h, w, _ = img.shape
        diagonal = math.sqrt(h**2 + w**2)
        
        # Inference
        mach_results = machinery_model.predict(img, save=False, verbose=False)[0]
        pers_results = person_model.predict(img, save=False, verbose=False)[0]
        
        # Format for Detector
        machines = []
        for box in mach_results.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            label = machinery_model.names[cls_id]
            
            if conf > 0.5:
                machines.append({
                    "label": label,
                    "bbox": (x1, y1, x2, y2),
                    "conf": conf
                })
                # Draw Box
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 165, 255), 2) # Orange
                cv2.putText(img, label, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2)

        persons = []
        for p_idx, box in enumerate(pers_results.boxes):
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            cls_id = int(box.cls[0]) # 0 is person in COCO
            
            if cls_id == 0 and conf > 0.3:
                # Fake track ID for single frame test
                # To test temporal persistence, we'd need video. 
                # For this frame test, we simulate "Enough Time Passed" by forcing timestamp?
                # Or we just visualise the distance line regardless of event trigger, 
                # but verify event trigger logic separately.
                # Actually, the 'process' method creates internal state.
                # If we send t0, it initializes.
                # If we want to see the event, we basically need to call it twice with elapsed time.
                
                track_id = p_idx + 1 
                persons.append({
                    "track_id": track_id,
                    "bbox": (x1, y1, x2, y2),
                    "conf": conf
                })
                # Draw Box
                cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 0), 2) # Blue
                cv2.putText(img, f"Person {track_id}", (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        # Run Logic (Pass 1 - Init)
        t0 = time.time()
        detector.process(persons, machines, w, h, now=t0)
        
        # Run Logic (Pass 2 - Trigger)
        # Simulate 2.0 seconds passing to force trigger all pending events
        t1 = t0 + 2.0 
        events = detector.process(persons, machines, w, h, now=t1)
        
        # Note: The visualizer should draw the line based on geometric distance, 
        # and color it based on what the Event says (or theoretical level).
        # Since 'events' only contains triggered events, we might miss 'Safe' lines.
        # So we repeat the distance calc here just for visualization.
        
        event_map = {e.person_id: e for e in events} # Map PID -> Event
        
        for p in persons:
            p_center = get_center(p["bbox"])
            
            # Find closest machine (visual only logic)
            closest_m = None
            min_dist = float('inf')
            
            for m in machines:
                m_center = get_center(m["bbox"])
                dist = math.sqrt((p_center[0]-m_center[0])**2 + (p_center[1]-m_center[1])**2)
                if dist < min_dist:
                    min_dist = dist
                    closest_m = m_center
            
            if closest_m:
                norm_dist = min_dist / diagonal
                
                # Default Green
                color = (0, 255, 0)
                thickness = 2
                status = f"Safe ({norm_dist:.2f})"
                
                # Check Logic Event
                if p["track_id"] in event_map:
                    evt = event_map[p["track_id"]]
                    if evt.severity == "CRITICAL":
                        color = (0, 0, 255) # Red
                        thickness = 4
                        status = f"CRITICAL ({norm_dist:.2f})"
                    elif evt.severity == "WARNING":
                        color = (0, 255, 255) # Yellow
                        thickness = 3
                        status = f"WARNING ({norm_dist:.2f})"
                
                # Draw Line
                cv2.line(img, p_center, closest_m, color, thickness)
                mid_x = int((p_center[0] + closest_m[0]) / 2)
                mid_y = int((p_center[1] + closest_m[1]) / 2)
                cv2.putText(img, status, (mid_x, mid_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # Save
        out_path = OUTPUT_DIR / img_path.name
        cv2.imwrite(str(out_path), img)
        logger.info(f"Saved {out_path}")

    logger.info("Verification complete.")

if __name__ == "__main__":
    main()
