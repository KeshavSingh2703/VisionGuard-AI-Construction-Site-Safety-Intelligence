"""Video loader for processing video files."""

import cv2
import numpy as np
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime, timedelta
import logging

from src.core.types import VideoFrame
from src.core.base import BaseStage
from src.core.exceptions import VideoProcessingError

logger = logging.getLogger(__name__)


class VideoLoader(BaseStage):
    """Load and process video files."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.frame_interval = self.config.get("frame_interval", 30)
        self.max_frames = self.config.get("max_frames", 1000)
        self.sample_rate = self.config.get("sample_rate", 1.0)
    
    def process(self, input_data: Any) -> Any:
        """Process video file or image."""
        if isinstance(input_data, str):
            path = Path(input_data)
        elif isinstance(input_data, Path):
            path = input_data
        else:
            raise ValueError(f"Unsupported input type: {type(input_data)}")
            
        suffix = path.suffix.lower()
        if suffix in ['.jpg', '.jpeg', '.png', '.bmp']:
            return self.load_image(str(path))
        else:
            return self.load_video(str(path))

    def load_image(self, image_path: str) -> List[VideoFrame]:
        """Load single image as a 1-frame video."""
        if not Path(image_path).exists():
            raise VideoProcessingError(f"Image file not found: {image_path}")
            
        try:
            # Read image
            frame = cv2.imread(image_path)
            if frame is None:
                raise VideoProcessingError(f"Failed to read image: {image_path}")
                
            height, width, _ = frame.shape
            
            # Create single video frame
            video_frame = VideoFrame(
                frame_number=0,
                timestamp=datetime.now(),
                image=frame,
                detections=[],
                metadata={
                    "fps": 0,
                    "width": width,
                    "height": height,
                    "total_frames": 1,
                    "source_type": "image"
                }
            )
            
            logger.info(f"Loaded image: {image_path} ({width}x{height})")
            return [video_frame]
            
        except Exception as e:
            logger.error(f"Failed to load image {image_path}: {e}")
            raise VideoProcessingError(f"Image loading failed: {e}") from e

    def load_video(self, video_path: str) -> List[VideoFrame]:
        """Load video and extract frames."""
        if not Path(video_path).exists():
            raise VideoProcessingError(f"Video file not found: {video_path}")
        
        try:
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                raise VideoProcessingError(f"Failed to open video: {video_path}")
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            logger.info(
                f"Loading video: {video_path}, "
                f"FPS: {fps}, Frames: {total_frames}, "
                f"Size: {width}x{height}"
            )
            
            frames = []
            frame_number = 0
            processed_count = 0
            
            while cap.isOpened() and processed_count < self.max_frames:
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                # Sample frames based on interval
                if frame_number % self.frame_interval == 0:
                    # Calculate timestamp
                    # Avoid division by zero if fps is 0/invalid
                    safe_fps = fps if fps > 0 else 30.0
                    timestamp = datetime.now() + timedelta(seconds=frame_number / safe_fps)
                    
                    video_frame = VideoFrame(
                        frame_number=frame_number,
                        timestamp=timestamp,
                        image=frame.copy(),
                        detections=[],
                        metadata={
                            "fps": fps,
                            "width": width,
                            "height": height,
                            "total_frames": total_frames
                        }
                    )
                    
                    frames.append(video_frame)
                    processed_count += 1
                
                frame_number += 1
            
            cap.release()
            logger.info(f"Loaded {len(frames)} frames from video")
            
            return frames
            
        except Exception as e:
            logger.error(f"Failed to load video {video_path}: {e}")
            raise VideoProcessingError(f"Video loading failed: {e}") from e
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Get video or image metadata."""
        path = Path(video_path)
        if path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
             frame = cv2.imread(video_path)
             if frame is None: raise VideoProcessingError("Invalid image")
             h, w, _ = frame.shape
             return {"fps": 0, "total_frames": 1, "width": w, "height": h, "duration": 0}

        try:
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                raise VideoProcessingError(f"Failed to open video: {video_path}")
            
            info = {
                "fps": cap.get(cv2.CAP_PROP_FPS),
                "total_frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                "duration": cap.get(cv2.CAP_PROP_FRAME_COUNT) / (cap.get(cv2.CAP_PROP_FPS) or 30.0)
            }
            
            cap.release()
            return info
            
        except Exception as e:
            logger.error(f"Failed to get video info: {e}")
            raise VideoProcessingError(f"Failed to get video info: {e}") from e

