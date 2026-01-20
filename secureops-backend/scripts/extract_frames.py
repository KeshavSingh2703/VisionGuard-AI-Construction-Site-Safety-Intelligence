import cv2
import argparse
from pathlib import Path
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_frames(input_video, output_dir, fps=1):
    input_path = Path(input_video)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        logger.error(f"Failed to open video: {input_path}")
        return
        
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(video_fps / fps)
    if frame_interval < 1:
        frame_interval = 1
        
    logger.info(f"Video FPS: {video_fps}. Extraction interval: {frame_interval} frames (approx {fps} FPS)")
    
    count = 0
    saved_count = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        if count % frame_interval == 0:
            frame_name = f"{input_path.stem}_frame_{count:06d}.jpg"
            out_file = output_path / frame_name
            cv2.imwrite(str(out_file), frame)
            saved_count += 1
            if saved_count % 10 == 0:
                logger.info(f"Saved {saved_count} frames...")
                
        count += 1
        
    cap.release()
    logger.info(f"Extraction complete. {saved_count} frames saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Extract frames from video for training dataset.")
    parser.add_argument("--input", type=str, required=True, help="Path to input video file")
    parser.add_argument("--output", type=str, required=True, help="Output directory for frames")
    parser.add_argument("--fps", type=float, default=1.0, help="Frames to extract per second")
    
    args = parser.parse_args()
    
    extract_frames(args.input, args.output, args.fps)

if __name__ == "__main__":
    main()
