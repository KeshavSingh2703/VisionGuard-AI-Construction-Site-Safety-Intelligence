from ultralytics import YOLO
import argparse

def train_ppe(data_config, epochs=100, imgsz=640, device="0"):
    # Load a model
    model = YOLO("yolov8s.pt")  # load a pretrained model (recommended for training)

    # Train the model
    results = model.train(
        data=data_config, 
        epochs=epochs, 
        imgsz=imgsz, 
        device=device,
        batch=16,
        name="ppe_detector",
        exist_ok=True,
        # Augmentation settings (can be defined in yaml or here)
        mosaic=1.0,
        mixup=0.1,
    )
    
    # Evaluate
    metrics = model.val()
    print(f"Validation map50-95: {metrics.box.map}")

    # Export
    success = model.export(format="onnx")
    print(f"Export success: {success}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train PPE Detector (Helmet/Vest)")
    parser.add_argument("--data", type=str, default="ppe_data.yaml", help="Path to data.yaml")
    parser.add_argument("--epochs", type=int, default=100, help="Number of epochs")
    parser.add_argument("--device", type=str, default="cpu", help="Device (cpu, mps, 0)")
    
    args = parser.parse_args()
    
    # For Mac M-series, use 'mps' if available, otherwise 'cpu'
    # '0' is for NVIDIA GPU
    device = args.device
    if device == "auto":
        import torch
        if torch.backends.mps.is_available():
            device = "mps"
        elif torch.cuda.is_available():
            device = "0"
        else:
            device = "cpu"
            
    train_ppe(args.data, args.epochs, device=device)
