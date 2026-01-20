import requests
import cv2
import os
import logging
from pathlib import Path
from ultralytics import YOLO

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
TEST_DIR = Path("helmet_test")
INPUT_DIR = TEST_DIR / "input_images"
OUTPUT_DIR = TEST_DIR / "output_images"
MODEL_PATH = Path("runs/detect/runs/detect/train_ppe/weights/best.pt")

IMAGE_URLS = [
    "https://github.com/njvisionpower/Safety-Helmet-Wearing-Dataset/raw/master/image/10.jpg",
    "https://github.com/njvisionpower/Safety-Helmet-Wearing-Dataset/raw/master/image/3.jpg",
    "https://github.com/njvisionpower/Safety-Helmet-Wearing-Dataset/raw/master/image/4.jpg",
    "https://github.com/njvisionpower/Safety-Helmet-Wearing-Dataset/raw/master/image/5.jpg",
    "https://github.com/njvisionpower/Safety-Helmet-Wearing-Dataset/raw/master/image/6.jpg"
]

# Colors (BGR)
COLOR_HELMET = (0, 255, 0)    # Green
COLOR_NO_HELMET = (0, 0, 255) # Red
COLOR_TEXT = (255, 255, 255)  # White

def setup_directories():
    """Create directory structure."""
    if TEST_DIR.exists():
        import shutil
        shutil.rmtree(TEST_DIR)
    
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created directories at {TEST_DIR}")

def download_images():
    """Download test images."""
    logger.info("Downloading images...")
    for url in IMAGE_URLS:
        filename = url.split('/')[-1]
        save_path = INPUT_DIR / filename
        
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(resp.content)
                logger.info(f"Downloaded {filename}")
            else:
                logger.error(f"Failed to download {url}: {resp.status_code}")
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")

def run_inference():
    """Run YOLO inference and save annotated images."""
    if not MODEL_PATH.exists():
        logger.error(f"Model not found at {MODEL_PATH}")
        logger.error("Please run scripts/train_model.py first!")
        return

    logger.info(f"Loading model from {MODEL_PATH}...")
    try:
        model = YOLO(MODEL_PATH)
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return

    input_files = list(INPUT_DIR.glob("*.jpg"))
    logger.info(f"Running inference on {len(input_files)} images...")

    for img_path in input_files:
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
                
                # Coordinates
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                
                # Determine Label & Color
                # 0 -> Helmet, 1 -> No Helmet
                if cls_id == 0:
                    label = f"Helmet {conf:.2f}"
                    color = COLOR_HELMET
                else:
                    label = f"No Helmet {conf:.2f}"
                    color = COLOR_NO_HELMET
                
                # Draw Box
                cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                
                # Draw Label Background
                (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                cv2.rectangle(img, (x1, y1 - 20), (x1 + w, y1), color, -1)
                
                # Draw Text
                cv2.putText(img, label, (x1, y1 - 5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_TEXT, 1)
            
            # Save output
            out_name = f"{img_path.stem}_helmet_result.jpg"
            out_path = OUTPUT_DIR / out_name
            cv2.imwrite(str(out_path), img)
            logger.info(f"Saved {out_name}")
            
        except Exception as e:
            logger.error(f"Failed to process {img_path.name}: {e}")

if __name__ == "__main__":
    setup_directories()
    download_images()
    run_inference()
    logger.info("Verification complete.")
