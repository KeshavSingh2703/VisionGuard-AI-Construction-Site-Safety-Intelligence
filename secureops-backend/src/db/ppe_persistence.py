from datetime import datetime
from typing import Dict, Any
import psycopg2
import psycopg2.extras
import logging

logger = logging.getLogger(__name__)

class PPEViolationRepository:
    def __init__(self, conn):
        self.conn = conn

    def save_violation(self, violation: Dict[str, Any]):
        """
        Save a single PPE violation to the database.
        
        Args:
            violation: Dictionary containing violation details.
                       Must have keys: track_id, missing_items, severity, 
                       start_time, end_time, confidence.
                       Optional: source_id.
        """
        query = """
        INSERT INTO ppe_violations (
            track_id,
            source_id,
            violation_type,
            missing_items,
            severity,
            start_time,
            end_time,
            duration_seconds,
            confidence
        )
        VALUES (
            %(track_id)s,
            %(source_id)s,
            %(violation_type)s,
            %(missing_items)s,
            %(severity)s,
            %(start_time)s,
            %(end_time)s,
            %(duration_seconds)s,
            %(confidence)s
        )
        """
        
        # Calculate duration if not present or pre-calculated
        start = violation["start_time"]
        end = violation["end_time"]
        
        # Ensure datetimes are accessible
        # PPERuleEngine returns ISO strings for start_time in generated dict? 
        # Actually it returned ISO for start_time but also a timestamp obj?
        # Let's check ppe_rules.py output format to be safe.
        # It returned: "start_time": isoformat, "timestamp": datetime object.
        # But here input might be flexible. 
        # We assume input has proper datetime objects or we parse them?
        # The prompt code calculated duration from start_time and end_time objects.
        
        if isinstance(start, str):
            start = datetime.fromisoformat(start)
        if isinstance(end, str):
            end = datetime.fromisoformat(end)

        duration = (end - start).total_seconds()

        payload = {
            "track_id": violation["track_id"],
            "source_id": violation.get("source_id"), # None if missing
            "violation_type": "PPE",
            "missing_items": violation["missing_items"],
            "severity": violation["severity"],
            "start_time": start,
            "end_time": end,
            "duration_seconds": duration,
            "confidence": violation["confidence"]
        }

        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(query, payload)
            self.conn.commit()
            # logger.info(f"Saved PPE violation for Track ID {violation['track_id']}")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to save PPE violation: {e}")
            raise

    def fetch(self, start_time: datetime, end_time: datetime) -> list:
        """
        Fetch PPE violations within a time range.
        """
        query = """
            SELECT * FROM ppe_violations
            WHERE start_time >= %s AND start_time <= %s
            ORDER BY start_time ASC
        """
        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(query, (start_time, end_time))
                rows = cur.fetchall()
                # RealDictCursor returns dicts, perfect for aggregator
                # We also normalize field names if needed, but 'event_time' concept maps to 'start_time' here
                # Aggregator will handle mapping.
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to fetch PPE violations: {e}")
            return []
