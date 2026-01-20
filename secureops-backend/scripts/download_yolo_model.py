"""Script to download YOLOv8 model."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ultralytics import YOLO
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_yolo_model(model_name: str = "yolov8n.pt", output_path: str = "models/yolov8n.pt"):
    """Download YOLOv8 model."""
    try:
        logger.info(f"Downloading {model_name}...")
        
        # Create models directory if it doesn't exist
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Download model (YOLO auto-downloads when you instantiate)
        model = YOLO(model_name)
        
        # Save to specified location
        model.save(output_path)
        
        logger.info(f"Model downloaded successfully to {output_path}")
        logger.info(f"Model size: {output_file.stat().st_size / (1024 * 1024):.2f} MB")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to download model: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Download YOLOv8 model")
    parser.add_argument(
        "--model",
        default="yolov8n.pt",
        help="Model name (yolov8n.pt, yolov8s.pt, yolov8m.pt, etc.)"
    )
    parser.add_argument(
        "--output",
        default="models/yolov8n.pt",
        help="Output path for model file"
    )
    
    args = parser.parse_args()
    
    success = download_yolo_model(args.model, args.output)
    sys.exit(0 if success else 1)

