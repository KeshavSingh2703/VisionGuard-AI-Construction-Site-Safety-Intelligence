import zipfile
import requests
import os
import shutil
import logging
import yaml
from pathlib import Path
from ultralytics import YOLO

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Config
DATA_URL = "https://github.com/ultralytics/assets/releases/download/v0.0.0/construction-ppe.zip"
DATA_DIR = Path("data/vest_dataset")
ZIP_PATH = Path("construction-ppe.zip")
CONFIG_PATH = Path("vest.yaml")

# Dataset specific logic
# We want to map dataset classes to:
TARGET_MAP = {
    0: ["vest", "safety vest", "safety_vest"], # New ID 0
    1: ["helmet", "hardhat", "hard hat", "hard_hat"] # New ID 1
}
# New names for YOLO
NEW_NAMES = {
    0: "vest",
    1: "helmet"
}

def download_dataset():
    """Download and extract dataset."""
    if DATA_DIR.exists():
        logger.info(f"Dataset directory {DATA_DIR} already exists.")
        return

    logger.info(f"Downloading dataset from {DATA_URL}...")
    try:
        r = requests.get(DATA_URL, stream=True)
        with open(ZIP_PATH, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.info("Extracting dataset...")
        with zipfile.ZipFile(ZIP_PATH, "r") as zip_ref:
            zip_ref.extractall(DATA_DIR)
        
        ZIP_PATH.unlink()
        logger.info("Dataset extracted.")
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise

def filter_dataset():
    """Parse original yaml, create mapping, and rewrite labels."""
    # Find original yaml
    original_yaml_files = list(DATA_DIR.rglob("*.yaml")) + list(DATA_DIR.rglob("*.yml"))
    if not original_yaml_files:
        logger.warning("No data.yaml found in dataset. Assuming standard mapping or raw data.")
        # If no yaml, we can't safely filter by name without manual inspection. 
        # But for this task, we assume the dataset is standard.
        return

    orig_yaml_path = original_yaml_files[0]
    with open(orig_yaml_path, 'r') as f:
        data = yaml.safe_load(f)
    
    names = data.get('names', {})
    # names can be dict {0: 'name'} or list ['name', ...]
    if isinstance(names, list):
        names = {i: n for i, n in enumerate(names)}
    
    logger.info(f"Original classes: {names}")

    # Build Map: Original ID -> New ID
    id_map = {}
    for orig_id, orig_name in names.items():
        lname = orig_name.lower().strip()
        
        # Check against target map
        mapped_to = None
        for new_id, variants in TARGET_MAP.items():
            if lname in variants:
                mapped_to = new_id
                break
        
        if mapped_to is not None:
            id_map[orig_id] = mapped_to
    
    logger.info(f"Class Mapping: {id_map}")
    
    if not id_map:
        logger.error("Could not find target classes (vest/helmet) in dataset!")
        return

    # Rewrite Labels
    label_files = list(DATA_DIR.rglob("*.txt"))
    logger.info(f"Filtering {len(label_files)} label files...")
    
    for lfile in label_files:
        with open(lfile, 'r') as f:
            lines = f.readlines()
        
        new_lines = []
        for line in lines:
            parts = line.strip().split()
            if not parts: continue
            
            try:
                cls_id = int(float(parts[0]))
                if cls_id in id_map:
                    new_id = id_map[cls_id]
                    # Replace first element
                    parts[0] = str(new_id)
                    new_lines.append(" ".join(parts))
            except ValueError:
                continue
        
        # Overwrite file
        with open(lfile, 'w') as f:
            f.write("\n".join(new_lines))

def create_config():
    """Create local vest.yaml."""
    # Locate images dir
    # Usually structure is data/vest_dataset/images/train or data/vest_dataset/construction-ppe/images/train
    # We'll search for 'train' dir inside 'images'
    
    img_dirs = list(DATA_DIR.rglob("images"))
    if not img_dirs:
        # Fallback assumption
        base_img = DATA_DIR 
    else:
        base_img = img_dirs[0] # Take the first one found
    
    # Check for train/val subdirs
    train_dir = base_img / "train"
    val_dir = base_img / "val" # or valid or test
    
    if not val_dir.exists():
        # sometimes it's 'valid'
        valid_search = list(base_img.glob("valid"))
        if valid_search:
            val_dir = valid_search[0]
            
    logger.info(f"Training dir: {train_dir}")
    
    config = {
        "train": str(train_dir.absolute()),
        "val": str(val_dir.absolute()),
        "names": NEW_NAMES
    }
    
    with open(CONFIG_PATH, 'w') as f:
        yaml.dump(config, f)
    logger.info(f"Config saved to {CONFIG_PATH}")

def reduce_dataset_size(keep_train=200, keep_val=50):
    """Reduce dataset size for faster CPU training verification."""
    logger.info(f"Reducing dataset: keeping {keep_train} train, {keep_val} val images...")
    
    for split, limit in [("train", keep_train), ("val", keep_val), ("valid", keep_val)]:
        img_dir = Path(DATA_DIR) / "images" / split
        lbl_dir = Path(DATA_DIR) / "labels" / split
        
        # Handle case where 'valid' might not exist if 'val' does, etc.
        # But we know standard structure usually has train/val
        if not img_dir.exists(): 
            continue
            
        # Get all images
        images = sorted(list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.png")) + list(img_dir.glob("*.jpeg")))
        
        if len(images) <= limit:
            continue
            
        logger.info(f" Trimming {split} from {len(images)} to {limit}...")
        
        # Files to remove
        to_remove = images[limit:]
        
        for img_p in to_remove:
            # Remove image
            img_p.unlink()
            
            # Remove corresponding label
            lbl_p = lbl_dir / (img_p.stem + ".txt")
            if lbl_p.exists():
                lbl_p.unlink()

def train():
    logger.info("Starting YOLOv8 training...")
    
    # Cleanup previous incomplete run if exists
    run_dir = Path("runs/detect/vest_detector")
    if run_dir.exists():
        import shutil
        shutil.rmtree(run_dir)
    
    model = YOLO("yolov8s.pt")
    
    model.train(
        data=str(CONFIG_PATH.absolute()),
        epochs=100,
        imgsz=640,
        batch=16,
        project="runs/detect",
        name="vest_detector",
        exist_ok=True
    )
    logger.info("Training complete.")

if __name__ == "__main__":
    download_dataset()
    filter_dataset()
    # reduce_dataset_size() # Skipped for M4 training - using full dataset
    
    # Check for MPS
    import torch
    if torch.backends.mps.is_available():
        logger.info("Apple MPS (Metal Performance Shaders) detected! Using GPU.")
        device = "mps"
    else:
        logger.warning("MPS not available. Fallback to CPU.")
        device = "cpu"

    model = YOLO("yolov8s.pt")

    model.train(
        data=str(CONFIG_PATH.absolute()),
        epochs=100,
        imgsz=640,
        batch=16, # Increased batch size for GPU efficiency if needed, but 16 is safe
        project="runs/detect",
        name="vest_detector",
        exist_ok=True,
        device=device,
        amp=False # Disable Mixed Precision to prevent MPS crashes on Apple Silicon
    )
