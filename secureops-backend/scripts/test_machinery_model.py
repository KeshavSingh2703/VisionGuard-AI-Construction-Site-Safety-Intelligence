import os
import shutil
import random
import logging
from pathlib import Path
from ultralytics import YOLO
import cv2

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
MODEL_PATH = Path("machinery_best.pt")
VAL_IMAGES_DIR = Path("machinery_dataset/images/val")
OUTPUT_DIR = Path("machinery_test_output")

def main():
    if not MODEL_PATH.exists():
        logger.error(f"Model not found at {MODEL_PATH}")
        return

    if not VAL_IMAGES_DIR.exists():
        logger.error(f"Validation images not found at {VAL_IMAGES_DIR}")
        return

    # Setup output
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load Model
    logger.info(f"Loading model from {MODEL_PATH}...")
    model = YOLO(str(MODEL_PATH))

    # Pick Random Images
    all_images = list(VAL_IMAGES_DIR.glob("*.jpg")) + list(VAL_IMAGES_DIR.glob("*.png"))
    if not all_images:
        logger.error("No images found in validation dir.")
        return
    
    selected_images = random.sample(all_images, min(5, len(all_images)))
    logger.info(f"Selected {len(selected_images)} images for testing.")

    # Run Inference
    for img_path in selected_images:
        logger.info(f"Processing {img_path.name}...")
        results = model.predict(str(img_path), save=False, verbose=False)
        
        result = results[0]
        img = result.orig_img
        
        # Draw Boxes
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            cls_name = model.names[cls_id]
            
            # Color: Excavator=Orange, Truck=Blue
            color = (0, 165, 255) if cls_name == "excavator" else (255, 0, 0)
            
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            label = f"{cls_name} {conf:.2f}"
            cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            logger.info(f"  -> Detected {cls_name} ({conf:.2f})")

        # Save
        out_path = OUTPUT_DIR / img_path.name
        cv2.imwrite(str(out_path), img)
        logger.info(f"Saved to {out_path}")

    logger.info("Testing complete.")

if __name__ == "__main__":
    main()
