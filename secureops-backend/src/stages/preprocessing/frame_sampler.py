"""Frame sampling utilities for video processing."""

from typing import List
from src.core.types import VideoFrame


class FrameSampler:
    """Sample frames from video."""
    
    @staticmethod
    def sample_frames(frames: List[VideoFrame], interval: int) -> List[VideoFrame]:
        """Sample frames at specified interval."""
        return [frame for i, frame in enumerate(frames) if i % interval == 0]
    
    @staticmethod
    def sample_by_time(frames: List[VideoFrame], max_frames: int) -> List[VideoFrame]:
        """Sample frames to get maximum number."""
        if len(frames) <= max_frames:
            return frames
        
        step = len(frames) // max_frames
        return [frames[i] for i in range(0, len(frames), step)]

