from ultralytics import YOLO
import argparse

def train_machinery(data_config, epochs=100, imgsz=640, device="0"):
    # Load a model
    model = YOLO("yolov8s.pt")  # load a pretrained model

    # Train the model
    results = model.train(
        data=data_config, 
        epochs=epochs, 
        imgsz=imgsz, 
        device=device,
        batch=16,
        name="machinery_detector",
        exist_ok=True
    )
    
    metrics = model.val()
    print(f"Validation map50-95: {metrics.box.map}")
    
    model.export(format="onnx")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Machinery Detector")
    parser.add_argument("--data", type=str, default="machinery_data.yaml", help="Path to data.yaml")
    parser.add_argument("--epochs", type=int, default=100, help="Number of epochs")
    parser.add_argument("--device", type=str, default="cpu", help="Device (cpu, mps, 0)")
    
    args = parser.parse_args()
    
    device = args.device
    if device == "auto":
        import torch
        if torch.backends.mps.is_available():
            device = "mps"
        elif torch.cuda.is_available():
            device = "0"
        else:
            device = "cpu"
            
    train_machinery(args.data, args.epochs, device=device)
