import cv2
import os
import logging
import random
from pathlib import Path
from ultralytics import YOLO

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
TEST_DIR = Path("vest_test")
OUTPUT_DIR = TEST_DIR / "output_images"
# Path to the trained model
# Note: Path might be nested depending on how many runs occurred. 
# We'll try the specific one first or use a glob if needed dynamically, but sticking to hardcoded based on known state.
MODEL_PATH = Path("runs/detect/runs/detect/vest_detector/weights/best.pt")
DATA_VAL_DIR = Path("data/vest_dataset/images/val")

# Colors (BGR)
COLOR_VEST = (0, 255, 0)      # Green
COLOR_HELMET = (255, 255, 0)  # Cyan (Optional)
COLOR_TEXT = (255, 255, 255)  # White

def setup_directories():
    """Create directory structure."""
    if OUTPUT_DIR.exists():
        import shutil
        shutil.rmtree(OUTPUT_DIR)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created output directory at {OUTPUT_DIR}")

def run_inference():
    """Run YOLO inference and save annotated images."""
    if not MODEL_PATH.exists():
        logger.error(f"Model not found at {MODEL_PATH}")
        return

    logger.info(f"Loading model from {MODEL_PATH}...")
    try:
        model = YOLO(MODEL_PATH)
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return

    # Pick random 5 images from validation set
    all_imgs = list(DATA_VAL_DIR.glob("*.jpg")) + list(DATA_VAL_DIR.glob("*.png")) + list(DATA_VAL_DIR.glob("*.jpeg"))
    if not all_imgs:
        logger.error(f"No validation images found in {DATA_VAL_DIR}")
        return
        
    test_imgs = random.sample(all_imgs, min(5, len(all_imgs)))
    logger.info(f"Running inference on {len(test_imgs)} images...")

    for img_path in test_imgs:
        try:
            # Inference
            results = model.predict(source=str(img_path), save=False, conf=0.25, verbose=False)
            
            # Load image for drawing
            img = cv2.imread(str(img_path))
            if img is None:
                continue

            result = results[0]
            
            # Draw detections
            for box in result.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                label_name = model.names[cls_id]
                
                # Coordinates
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                
                # Determine Label & Color
                # 0 -> vest, 1 -> helmet
                if label_name == "vest":
                    color = COLOR_VEST
                    label_str = f"Vest {conf:.2f}"
                elif label_name == "helmet":
                    color = COLOR_HELMET
                    label_str = f"Helmet {conf:.2f}"
                else:
                    color = (0, 0, 255) # Red for unknown
                    label_str = f"{label_name} {conf:.2f}"
                
                # Draw Box
                cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                
                # Draw Label Background
                (w, h), _ = cv2.getTextSize(label_str, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                cv2.rectangle(img, (x1, y1 - 20), (x1 + w, y1), color, -1)
                
                # Draw Text
                cv2.putText(img, label_str, (x1, y1 - 5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_TEXT, 1)
            
            # Save output
            out_name = f"{img_path.stem}_result.jpg"
            out_path = OUTPUT_DIR / out_name
            cv2.imwrite(str(out_path), img)
            logger.info(f"Saved {out_name}")
            
        except Exception as e:
            logger.error(f"Failed to process {img_path.name}: {e}")

if __name__ == "__main__":
    setup_directories()
    run_inference()
    logger.info("Vest verification complete.")
