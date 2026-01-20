"""Violation counting and aggregation."""

from typing import List, Dict, Any, Optional
from sqlalchemy import func
from src.db.session import get_db_session
from src.db.models import Detection, SafetyViolation, ProximityEvent
import logging

logger = logging.getLogger(__name__)


class ViolationCounter:
    """Count and aggregate violations."""
    
    def count_violations(self, video_id: Optional[str] = None) -> Dict[str, Any]:
        """Count violations."""
        try:
            with get_db_session() as session:
                # 1. Total People (Detections)
                det_query = session.query(func.count(Detection.id)).filter(
                    Detection.class_name == 'person'
                )
                if video_id:
                    det_query = det_query.filter(Detection.video_id == video_id)
                people_count = det_query.scalar()
                
                # 2. Safety Violations (PPE, Zone)
                sv_query = session.query(SafetyViolation)
                if video_id:
                    sv_query = sv_query.filter(SafetyViolation.video_id == video_id)
                
                total_sv = sv_query.count()
                ppe_violations = sv_query.filter(SafetyViolation.violation_type.like('%helmet%') | SafetyViolation.violation_type.like('%vest%')).count()
                zone_violations = sv_query.filter(SafetyViolation.violation_type == 'zone_intrusion').count() # Ensure consistency with Enums used
                
                # 3. Proximity Events
                pe_query = session.query(ProximityEvent)
                if video_id:
                    pe_query = pe_query.filter(ProximityEvent.video_id == video_id)
                prox_count = pe_query.count()
                
                return {
                    "total_people": people_count,
                    "ppe_violations": ppe_violations,
                    "zone_violations": zone_violations,
                    "proximity_violations": prox_count,
                    "total_violations": total_sv + prox_count
                }
        except Exception as e:
            logger.error(f"Failed to count violations: {e}")
            return {
                "total_people": 0,
                "ppe_violations": 0,
                "zone_violations": 0,
                "proximity_violations": 0,
                "total_violations": 0
            }

