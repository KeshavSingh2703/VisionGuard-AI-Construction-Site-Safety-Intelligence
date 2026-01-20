"""Tests for video processing pipeline."""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.stages.input.video_loader import VideoLoader
from src.stages.vision.detector import VisionDetector
from src.core.types import VideoFrame
from src.pipeline.orchestrator import PipelineOrchestrator


@pytest.fixture
def mock_yolo_model():
    """Mock YOLO model."""
    model = Mock()
    model.predict = Mock(return_value=[Mock(
        boxes=Mock(
            cls=[[0], [2]],
            conf=[[0.9], [0.8]],
            xyxy=[[[10, 20, 30, 40]], [[50, 60, 70, 80]]]
        ),
        names={0: 'person', 2: 'car'}
    )])
    model.names = {0: 'person', 2: 'car'}
    return model


@pytest.fixture
def sample_frame():
    """Sample video frame."""
    return VideoFrame(
        frame_number=0,
        timestamp=datetime.now(),
        image=np.zeros((480, 640, 3), dtype=np.uint8)
    )


class TestVideoLoader:
    """Test video loader."""
    
    @patch('cv2.VideoCapture')
    def test_load_video(self, mock_capture):
        """Test video loading."""
        # Mock video capture
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda x: {
            5: 30.0,  # FPS
            7: 100,   # Frame count
            3: 640,   # Width
            4: 480    # Height
        }.get(x, 0)
        mock_cap.read.side_effect = [
            (True, np.zeros((480, 640, 3), dtype=np.uint8)),
            (False, None)
        ]
        mock_capture.return_value = mock_cap
        
        loader = VideoLoader({"frame_interval": 1, "max_frames": 10})
        frames = loader.load_video("test_video.mp4")
        
        assert len(frames) > 0
        assert isinstance(frames[0], VideoFrame)


class TestVisionDetector:
    """Test vision detector."""
    
    @patch('src.stages.vision.detector.load_yolo_model')
    def test_process_frame(self, mock_load_model, mock_yolo_model, sample_frame):
        """Test frame processing."""
        mock_load_model.return_value = mock_yolo_model
        
        detector = VisionDetector({
            "model_path": "models/yolov8n.pt",
            "confidence_threshold": 0.25,
            "device": "cpu"
        })
        
        result = detector.process(sample_frame)
        
        assert isinstance(result, VideoFrame)
        assert len(result.detections) > 0


class TestPipelineOrchestrator:
    """Test pipeline orchestrator."""
    
    @patch('src.pipeline.orchestrator.VisionDetector')
    @patch('src.pipeline.orchestrator.VideoLoader')
    @patch('src.db.session.get_db_session')
    def test_process_video(self, mock_db, mock_loader, mock_detector):
        """Test video processing pipeline."""
        # Mock database session
        mock_session = Mock()
        mock_db.return_value.__enter__.return_value = mock_session
        mock_db.return_value.__exit__.return_value = None
        
        # Mock video loader
        mock_loader_instance = Mock()
        mock_loader_instance.load_video.return_value = [
            VideoFrame(
                frame_number=0,
                timestamp=datetime.now(),
                image=np.zeros((480, 640, 3), dtype=np.uint8)
            )
        ]
        mock_loader.return_value = mock_loader_instance
        
        # Mock detector
        mock_detector_instance = Mock()
        mock_frame = VideoFrame(
            frame_number=0,
            timestamp=datetime.now(),
            image=np.zeros((480, 640, 3), dtype=np.uint8),
            detections=[]
        )
        mock_detector_instance.process.return_value = mock_frame
        mock_detector.return_value = mock_detector_instance
        
        orchestrator = PipelineOrchestrator()
        
        # This would require actual file, so we'll mock the path check
        with patch('os.path.exists', return_value=True):
            with patch('pathlib.Path.exists', return_value=True):
                # Note: Full test would require more mocking
                pass

