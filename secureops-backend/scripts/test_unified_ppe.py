import cv2
import os
import requests
import logging
from pathlib import Path
from typing import List
from datetime import datetime
from ultralytics import YOLO

# Project imports (ensure pythonpath is set)
import sys
sys.path.append(os.getcwd())
from src.stages.vision.ppe_rules import PPERuleEngine
from src.core.types import VideoFrame, Detection

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Config
OUTPUT_DIR = Path("unified_test/output_images")
HELMET_MODEL_PATH = Path("runs/detect/runs/detect/train_ppe/weights/best.pt") # Path from train_model.py
VEST_MODEL_PATH = Path("runs/detect/runs/detect/vest_detector/weights/best.pt") # Path from train_vest_model.py
PERSON_MODEL_NAME = "yolov8n.pt"

import zipfile
import random
import shutil

# Dataset Source (Reliable)
DATASET_URL = "https://github.com/ultralytics/assets/releases/download/v0.0.0/construction-ppe.zip"

def setup_dirs():
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def download_images():
    logger.info("Downloading dataset zip (reliable source)...")
    zip_path = Path("temp_ppe.zip")
    extract_root = Path("temp_ppe_extract")
    
    # Clean previous temp
    if extract_root.exists(): shutil.rmtree(extract_root)
    if zip_path.exists(): zip_path.unlink()
    
    images = []
    try:
        # Download
        r = requests.get(DATASET_URL, stream=True)
        if r.status_code != 200:
            logger.error(f"Failed to download zip: {r.status_code}")
            return []
            
        with open(zip_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Extract
        logger.info("Extracting...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_root)
            
        # Find images
        # Structure is usually construction-ppe/images/train/ or similar
        # We search recursively for .jpg
        all_jpgs = list(extract_root.rglob("*.jpg"))
        logger.info(f"Found {len(all_jpgs)} images in archive.")
        
        if not all_jpgs:
            logger.error("No images found in zip.")
            return []
            
        # Select 20
        selected = random.sample(all_jpgs, min(20, len(all_jpgs)))
        
        # Move to OUTPUT_DIR
        for i, src in enumerate(selected):
            dst = OUTPUT_DIR / f"test_img_{i:02d}.jpg"
            shutil.move(str(src), str(dst))
            images.append(dst)
            
        logger.info(f"Selected {len(images)} images for testing.")
        
    except Exception as e:
        logger.error(f"Error handling dataset zip: {e}")
    finally:
        # Cleanup
        if zip_path.exists(): zip_path.unlink()
        if extract_root.exists(): shutil.rmtree(extract_root)
        
    return images

def load_models():
    logger.info("Loading models...")
    models = {}
    try:
        models["person"] = YOLO(PERSON_MODEL_NAME)
        models["helmet"] = YOLO(str(HELMET_MODEL_PATH))
        models["vest"] = YOLO(str(VEST_MODEL_PATH))
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        sys.exit(1)
    return models

def run_test():
    setup_dirs()
    images = download_images()
    
    if not images:
        logger.error("No images downloaded.")
        return

    models = load_models()
    
    # Init Rule Engine in Snapshot Mode (no smoothing)
    # config: smoothing_window = 0.0
    rule_engine = PPERuleEngine(config={"smoothing_window": 0.0, "compliance_buffer": 0.0})
    
    logger.info("Running inference...")
    
    for img_path in images:
        try:
            img = cv2.imread(str(img_path))
            if img is None: continue
            
            # --- 1. Detect Persons ---
            # Class 0 = person in COCO
            person_results = models["person"].predict(img, classes=[0], verbose=False)
            
            # --- 2. Detect Helmets ---
            helmet_results = models["helmet"].predict(img, verbose=False)
            
            # --- 3. Detect Vests ---
            vest_results = models["vest"].predict(img, verbose=False)
            
            # --- 4. Assemble Detections ---
            detections = []
            
            # Process Persons
            for r in person_results: # Should be 1 result object per image
                for box in r.boxes:
                    x1, y1, x2, y2 = map(float, box.xyxy[0])
                    # Create a deterministic fake track_id based on x coordinate for this static test
                    # In real vid, tracker provides this.
                    # We sort mainly to be consistent? 
                    # Here we just assign ID=1,2,3...
                   
                    # We need to spatially associate detections to this person? 
                    # Actually, the rule engine groups by track_id. 
                    # But our detectors are separate.
                    # WE NEED LOGIC TO ASSOCIATE HELMET/VEST TO PERSON ID.
                    # Simple heuristic: Intersection/Containment.
                    pass 

            # Let's simplify: 
            # We will generate a list of all detections.
            # Then we need to assign track_ids to them so Rule Engine can group them.
            # Strategy:
            # 1. List all Persons. Assign ID 1..N.
            # 2. List all Equipment. Assign to closest Person ID (if overlaps).
            
            persons_list = []
            equipment_list = []
            
            # Collect Persons
            for box in person_results[0].boxes:
                persons_list.append({
                    "bbox": box.xyxy[0].tolist(),
                    "conf": float(box.conf[0])
                })
            
            # Collect Helmets
            for box in helmet_results[0].boxes:
                cls_name = models["helmet"].names[int(box.cls[0])]
                # Map trained classes to normalized names if needed
                # Helmet model classes: 0->helmet, 1->no_helmet (from our training script)
                # But wait, did we map 0->helmet, 1->no_helmet? 
                # scripts/train_model.py used synthetic labels: 0=Helmet, 1=No Helmet.
                norm_name = "helmet" if cls_name == "helmet" or int(box.cls[0]) == 0 else "no_helmet"
                if int(box.cls[0]) == 1: norm_name = "no_helmet"
                
                equipment_list.append({
                    "bbox": box.xyxy[0].tolist(),
                    "conf": float(box.conf[0]),
                    "class": norm_name
                })

            # Collect Vests
            for box in vest_results[0].boxes:
                cls_name = models["vest"].names[int(box.cls[0])]
                # Vest model classes: 0->vest, 1->helmet (optional).
                # We care about vest.
                if cls_name == "vest" or int(box.cls[0]) == 0:
                     equipment_list.append({
                        "bbox": box.xyxy[0].tolist(),
                        "conf": float(box.conf[0]),
                        "class": "vest"
                    })
            
            # Associate
            final_detections = []
            
            for i, p in enumerate(persons_list):
                track_id = i + 1
                px1, py1, px2, py2 = p["bbox"]
                
                # Add Person Detection
                final_detections.append(Detection(
                    class_id=0, class_name="person", confidence=p["conf"],
                    bbox=(px1, py1, px2, py2), frame_number=0, timestamp=datetime.now(),
                    metadata={"track_id": track_id}
                ))
                
                # Find Equipment for this person
                for eq in equipment_list:
                    ex1, ey1, ex2, ey2 = eq["bbox"]
                    ecx, ecy = (ex1+ex2)/2, (ey1+ey2)/2
                    
                    # Check center overlap
                    if px1 <= ecx <= px2 and py1 <= ecy <= py2:
                        final_detections.append(Detection(
                            class_id=99, class_name=eq["class"], confidence=eq["conf"],
                            bbox=(ex1, ey1, ex2, ey2), frame_number=0, timestamp=datetime.now(),
                            metadata={"track_id": track_id}
                        ))

            # --- 5. Rule Engine ---
            frame = VideoFrame(
                frame_number=0, timestamp=datetime.now(), image=None, detections=final_detections
            )
            
            violations = rule_engine.check_compliance(frame)
            
            # --- 6. Visualization ---
            for det in final_detections:
                x1, y1, x2, y2 = map(int, det.bbox)
                
                if det.class_name == "person":
                    color = (255, 0, 0) # Blue
                    cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(img, f"ID:{det.metadata['track_id']}", (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                
                elif det.class_name == "helmet":
                    color = (0, 255, 0) # Green
                    cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                elif det.class_name == "no_helmet":
                     color = (0, 0, 255) # Red
                     cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                
                elif det.class_name == "vest":
                    color = (255, 255, 0) # Cyan
                    cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            
            # Draw Violations
            annotated_y = 30
            for v in violations:
                tid = v["track_id"]
                missing = v["missing_items"]
                text = f"VIOLATION ID {tid}: Missing {', '.join(missing)}"
                
                # Draw Box on Image (Top Left)
                cv2.putText(img, text, (10, annotated_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                annotated_y += 30
                
                # Highlight Person Box Red
                # Find person det again
                for det in final_detections:
                    if det.class_name == "person" and det.metadata["track_id"] == tid:
                         x1, y1, x2, y2 = map(int, det.bbox)
                         cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 4)

            
            # Save
            out_name = img_path.name
            out_full = OUTPUT_DIR / out_name
            cv2.imwrite(str(out_full), img)
            logger.info(f"Processed {out_name} - Violations: {len(violations)}")
            
        except Exception as e:
            logger.error(f"Error processing {img_path}: {e}")

if __name__ == "__main__":
    run_test()
