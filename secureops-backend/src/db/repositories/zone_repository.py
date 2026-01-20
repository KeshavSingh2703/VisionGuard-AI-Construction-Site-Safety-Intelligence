import psycopg2
from psycopg2.extras import execute_values
from typing import List, Dict


class ZoneEventRepository:
    def __init__(self, conn: psycopg2.extensions.connection):
        self.conn = conn

    def save_events(self, upload_id: str, events: List[Dict]):
        """
        Save zone violation events to the database.
        
        Args:
            upload_id: UUID string for the upload/session.
            events: List of dicts (from ZoneViolation.to_dict()).
        """
        if not events:
            return

        rows = [
            (
                upload_id,
                e["object_id"],
                e["object_type"],
                e["zone_id"],
                e["timestamp"],
            )
            for e in events
        ]

        sql = """
            INSERT INTO zone_events (
                upload_id,
                object_id,
                object_type,
                zone_id,
                event_time
            )
            VALUES %s
        """

        with self.conn.cursor() as cur:
            execute_values(cur, sql, rows)

        self.conn.commit()

    def fetch(self, start_time, end_time) -> List[Dict]:
        """
        Fetch zone events within a time range.
        """
        query = """
            SELECT * FROM zone_events
            WHERE event_time >= %s AND event_time <= %s
            ORDER BY event_time ASC
        """
        try:
            from psycopg2.extras import RealDictCursor
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (start_time, end_time))
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            print(f"Failed to fetch zone events: {e}")
            return []
