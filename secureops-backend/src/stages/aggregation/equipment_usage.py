"""Equipment usage aggregation."""

from typing import List, Dict, Any, Optional
from sqlalchemy import func
from src.db.session import get_db_session
from src.db.models import Detection
import logging

logger = logging.getLogger(__name__)


class EquipmentUsageAggregator:
    """Aggregate equipment usage statistics."""
    
    def aggregate(self, video_id: Optional[str] = None) -> Dict[str, Any]:
        """Aggregate equipment usage."""
        try:
            with get_db_session() as session:
                query = session.query(
                    Detection.class_name,
                    func.count(Detection.id).label('count'),
                    func.avg(Detection.confidence).label('avg_confidence')
                ).filter(
                    Detection.class_name.in_(['car', 'bus', 'truck'])
                )
                
                if video_id:
                    query = query.filter(Detection.video_id == video_id)
                
                results = query.group_by(Detection.class_name).all()
                
                return {
                    "equipment": [
                        {
                            "type": row.class_name,
                            "count": row.count,
                            "avg_confidence": float(row.avg_confidence)
                        }
                        for row in results
                    ]
                }
        except Exception as e:
            logger.error(f"Failed to aggregate equipment usage: {e}")
            return {"equipment": []}

