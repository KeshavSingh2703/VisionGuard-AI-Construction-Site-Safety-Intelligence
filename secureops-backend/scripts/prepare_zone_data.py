import os
import shutil
import random
import yaml
import logging
from pathlib import Path
from PIL import Image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
SOURCE_DIRS = [
    Path("machinery_dataset/images/val"),
    # Path("construction-ppe/test/images") # If exists, but let's stick to what we know works
]
DEST_DIR = Path("dataset/restricted_zones")
IMAGES_DIR = DEST_DIR / "images"
POLYGONS_FILE = DEST_DIR / "polygons.yaml"

def main():
    # 1. Setup Dirs
    if DEST_DIR.exists():
        shutil.rmtree(DEST_DIR)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    
    # 2. Collect Images
    all_images = []
    for d in SOURCE_DIRS:
        if d.exists():
            all_images.extend(list(d.glob("*.jpg")) + list(d.glob("*.png")))
    
    # Take a subset of 50 images for this dataset
    selected_images = random.sample(all_images, min(50, len(all_images)))
    logger.info(f"Selected {len(selected_images)} images for Restricted Zone dataset.")
    
    # 3. Copy Images and Define Polygons
    # We will define synthetic polygons.
    # Logic: 
    # - Type A: Left Half Restricted
    # - Type B: Bottom Right Corner Restricted
    # - Type C: Center Box Restricted
    
    polygons = {}
    
    for i, img_path in enumerate(selected_images):
        # file copy
        dest_path = IMAGES_DIR / img_path.name
        shutil.copy(str(img_path), str(dest_path))
        
        # Get dimensions
        with Image.open(dest_path) as im:
            w, h = im.size
        
        # Define Polygon
        poly_type = i % 3
        points = []
        
        if poly_type == 0: # Left Half
            # (0,0) -> (w/2, 0) -> (w/2, h) -> (0, h)
            points = [[0, 0], [int(w/2), 0], [int(w/2), h], [0, h]]
            name = "Left_Zone"
            
        elif poly_type == 1: # Bottom Right
            # (w/2, h/2) -> (w, h/2) -> (w, h) -> (w/2, h)
            points = [[int(w/2), int(h/2)], [w, int(h/2)], [w, h], [int(w/2), h]]
            name = "Corner_Zone"
            
        else: # Center Box
            # 25% margin
            m_w = int(w * 0.25)
            m_h = int(h * 0.25)
            # (mW, mH) -> (w-mW, mH) -> (w-mW, h-mH) -> (mW, h-mH)
            points = [
                [m_w, m_h],
                [w - m_w, m_h],
                [w - m_w, h - m_h],
                [m_w, h - m_h]
            ]
            name = "Center_Risk"
            
        polygons[img_path.name] = {
            "name": name,
            "points": points # integer pixels
        }
        
    # 4. Save YAML
    with open(POLYGONS_FILE, 'w') as f:
        yaml.dump(polygons, f)
        
    logger.info(f"Created {POLYGONS_FILE} with {len(polygons)} definitions.")
    logger.info("Data preparation complete.")

if __name__ == "__main__":
    main()
