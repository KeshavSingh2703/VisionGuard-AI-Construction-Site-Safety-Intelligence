import os
import yaml
import logging
import cv2
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Config
DATA_DIR = Path("data")
FRAMES_DIR = DATA_DIR / "frames"
ZONES_DIR = DATA_DIR / "zones"
OUTPUT_YAML = ZONES_DIR / "polygons.yaml"

def main():
    ZONES_DIR.mkdir(parents=True, exist_ok=True)
    
    if not FRAMES_DIR.exists():
        logger.error(f"{FRAMES_DIR} does not exist. Run extract_frames.py first.")
        return

    # Find all videos
    video_dirs = [d for d in FRAMES_DIR.iterdir() if d.is_dir()]
    
    all_zones = {}
    
    for v_dir in video_dirs:
        video_name = v_dir.name
        frames = sorted(list(v_dir.glob("*.jpg")))
        
        if not frames:
            continue
            
        # Read first frame for dims
        im = cv2.imread(str(frames[0]))
        h, w, _ = im.shape
        
        # Define Synthetic Zone: Left 30%
        # (0,0) -> (0.3w, 0) -> (0.3w, h) -> (0, h)
        x_limit = int(w * 0.3)
        
        polygon = [
            [0, 0],
            [x_limit, 0],
            [x_limit, h],
            [0, h]
        ]
        
        logger.info(f"Video {video_name}: Zone defined as Left 30% (x < {x_limit})")
        
        # Apply to all frames
        for f_path in frames:
            # key: video_name/frame_name
            # frame_id = f"{video_name}/{f_path.name}"
            # User format example: frame_id -> list of zones.
            # I will key by the relative path since that's unique.
            rel_path = f_path.relative_to(FRAMES_DIR)
            frame_id = str(rel_path)
            
            all_zones[frame_id] = [
                {
                    "zone_id": "zone_left_30",
                    "polygon": polygon
                }
            ]
            
    with open(OUTPUT_YAML, 'w') as f:
        yaml.dump(all_zones, f)
        
    logger.info(f"Generatd zones for {len(all_zones)} frames at {OUTPUT_YAML}")

if __name__ == "__main__":
    main()
