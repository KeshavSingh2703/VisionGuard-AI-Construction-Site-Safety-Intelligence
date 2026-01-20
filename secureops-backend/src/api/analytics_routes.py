"""Analytics routes."""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from sqlalchemy import func
import logging

from src.db.session import get_db_session
from src.db.models import Detection, Upload, User
from src.stages.aggregation.equipment_usage import EquipmentUsageAggregator
from src.stages.aggregation.violation_counter import ViolationCounter
from src.api.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/summary")
async def get_summary(
    video_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get analytics summary."""
    try:
        with get_db_session() as session:
            # Total detections
            query = session.query(func.count(Detection.id))
            if video_id:
                query = query.filter(Detection.video_id == video_id)
            total_detections = query.scalar()
            
            # Detections by class
            class_query = session.query(
                Detection.class_name,
                func.count(Detection.id).label('count')
            )
            if video_id:
                class_query = class_query.filter(Detection.video_id == video_id)
            class_counts = {
                row.class_name: row.count
                for row in class_query.group_by(Detection.class_name).all()
            }
            
            # Total videos
            total_videos = session.query(func.count(Upload.id)).scalar()
            
            return {
                "total_detections": total_detections,
                "detections_by_class": class_counts,
                "total_videos": total_videos,
                "video_id": video_id
            }
    except Exception as e:
        logger.error(f"Failed to get summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/equipment")
async def get_equipment_usage(
    video_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get equipment usage statistics."""
    try:
        aggregator = EquipmentUsageAggregator()
        return aggregator.aggregate(video_id)
    except Exception as e:
        logger.error(f"Failed to get equipment usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/violations")
async def get_violations(
    video_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get violation statistics."""
    try:
        counter = ViolationCounter()
        return counter.count_violations(video_id)
    except Exception as e:
        logger.error(f"Failed to get violations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

