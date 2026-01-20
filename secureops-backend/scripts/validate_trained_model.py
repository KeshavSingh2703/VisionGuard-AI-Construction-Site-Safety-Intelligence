import sys
from ultralytics import YOLO

def main():
    model_path = "/Users/girijeshkumarsingh/Downloads/AI-Powered Construction Site Monitoring/secureops-backend/runs/detect/models/training/ppe_yolo11n/weights/best.pt"
    try:
        model = YOLO(model_path)
        print(f"✅ Model loaded successfully from {model_path}")
        print("Classes:", model.names)
        
        # Simple inference test
        # Create a dummy image or just skip if no image provided
        import numpy as np
        img = np.zeros((640, 640, 3), dtype=np.uint8)
        res = model(img)
        print("✅ Inference test passed")
        
    except Exception as e:
        print(f"❌ Validation Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
