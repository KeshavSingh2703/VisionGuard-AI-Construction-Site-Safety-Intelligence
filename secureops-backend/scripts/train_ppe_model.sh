#!/bin/bash
# Train/Resume YOLOv11n on Construction-PPE Dataset (Mac M4 Safe Stability Config)

# Validation of Environment
echo "Checking Ultralytics version..."
pip show ultralytics | grep Version

# Set Output Directory
PROJECT_DIR="runs/detect/models/training"
NAME="ppe_yolo11n"
LAST_CHECKPOINT="$PROJECT_DIR/$NAME/weights/last.pt"

mkdir -p $PROJECT_DIR

echo "🚀 Starting YOLOv11 Training on MPS (SAFE MODE)..."

# Resume Logic
if [ -f "$LAST_CHECKPOINT" ]; then
    echo "🔄 Resuming from last checkpoint: $LAST_CHECKPOINT"
    yolo detect train \
        model="$LAST_CHECKPOINT" \
        data=construction-ppe.yaml \
        epochs=50 \
        imgsz=640 \
        batch=4 \
        workers=0 \
        device=mps \
        cache=False \
        amp=False \
        resume=True \
        patience=10 \
        project="$PROJECT_DIR" \
        name="$NAME" \
        exist_ok=True \
        verbose=True
else
    echo "🆕 Starting fresh training (Stability Optimized)"
    yolo detect train \
        model=yolo11n.pt \
        data=construction-ppe.yaml \
        epochs=50 \
        imgsz=640 \
        batch=4 \
        workers=0 \
        device=mps \
        cache=False \
        amp=False \
        patience=10 \
        project="$PROJECT_DIR" \
        name="$NAME" \
        exist_ok=True \
        verbose=True
fi

echo "✅ Training Process Finished."
