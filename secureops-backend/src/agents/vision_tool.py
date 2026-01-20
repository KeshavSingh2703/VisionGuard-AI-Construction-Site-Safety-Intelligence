"""Vision summary tool for LangChain agent."""

from typing import Optional, Dict, Any
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from sqlalchemy import func
import logging

from src.db.session import get_db_session
from src.db.models import Detection, Upload

logger = logging.getLogger(__name__)


class VisionToolInput(BaseModel):
    """Input for vision tool."""
    video_id: str = Field(description="Video ID to analyze")
    summary_type: str = Field(default="general", description="Type of summary: general, safety, activity")


class VisionTool(BaseTool):
    """Vision summary tool for analyzing video detections."""
    
    name = "vision_summary"
    description = """
    Use this tool to get summaries of video analysis results.
    This tool can provide:
    - General video summary (detections, activity levels)
    - Safety analysis (PPE compliance, proximity violations)
    - Activity analysis (people count, machinery usage)
    
    Input should include the video_id and optionally summary_type.
    """
    args_schema = VisionToolInput
    
    def _run(self, video_id: str, summary_type: str = "general") -> str:
        """Generate vision summary."""
        try:
            with get_db_session() as session:
                # Confirm upload exists
                upload = session.query(Upload).filter(Upload.id == video_id).first()
                if not upload:
                    return f"Video {video_id} not found."

                # Get detection summary (if populated)
                detections = session.query(Detection).filter(
                    Detection.video_id == video_id
                ).all()
                
                if not detections:
                    return f"No detections found for video {video_id}."
                
                # Generate summary based on type
                if summary_type == "safety":
                    return self._generate_safety_summary(detections)
                elif summary_type == "activity":
                    return self._generate_activity_summary(detections)
                else:
                    return self._generate_general_summary(detections, video_id)
                    
        except Exception as e:
            logger.error(f"Vision tool error: {e}")
            return f"Error generating summary: {str(e)}"
    
    def _generate_general_summary(self, detections: list, video_id: str) -> str:
        """Generate general video summary."""
        frame_count = len({d.frame_number for d in detections})
        summary = f"Video Summary for {video_id}:\n\n"
        summary += f"Total Frames (counted via detections): {frame_count}\n"
        summary += f"Total Detections: {len(detections)}\n\n"
        
        # Count by class
        class_counts = {}
        for det in detections:
            class_counts[det.class_name] = class_counts.get(det.class_name, 0) + 1
        
        summary += "Detections by Type:\n"
        for class_name, count in sorted(class_counts.items(), key=lambda x: -x[1]):
            summary += f"  - {class_name}: {count}\n"
        
        return summary
    
    def _generate_safety_summary(self, detections: list) -> str:
        """Generate safety-focused summary."""
        summary = "Safety Analysis:\n\n"
        
        people = [d for d in detections if d.class_name == "person"]
        machinery = [d for d in detections if d.class_name in ["car", "bus", "truck"]]
        
        summary += f"People Detected: {len(people)}\n"
        summary += f"Machinery Detected: {len(machinery)}\n\n"
        
        # Note: PPE and proximity checks would require additional processing
        summary += "Note: Detailed PPE compliance and proximity analysis requires frame-by-frame processing."
        
        return summary
    
    def _generate_activity_summary(self, detections: list) -> str:
        """Generate activity-focused summary."""
        summary = "Activity Analysis:\n\n"
        
        # Group by frame
        frame_detections = {}
        for det in detections:
            if det.frame_number not in frame_detections:
                frame_detections[det.frame_number] = []
            frame_detections[det.frame_number].append(det)
        
        summary += f"Active Frames: {len(frame_detections)}\n"
        summary += f"Average Detections per Frame: {len(detections) / len(frame_detections) if frame_detections else 0:.1f}\n"
        
        return summary
    
    async def _arun(self, video_id: str, summary_type: str = "general") -> str:
        """Async version."""
        return self._run(video_id, summary_type)

