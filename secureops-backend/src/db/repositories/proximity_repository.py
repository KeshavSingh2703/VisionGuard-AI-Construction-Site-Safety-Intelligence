import psycopg2
from psycopg2.extras import execute_values
from typing import List, Dict


class ProximityEventRepository:
    def __init__(self, conn: psycopg2.extensions.connection):
        self.conn = conn

    def save_events(
        self,
        upload_id: str,
        events: List[Dict],
    ) -> None:
        """
        Persist proximity events to PostgreSQL.
        Expects events as list of dicts from ProximityEvent.to_dict()
        """

        if not events:
            return

        rows = [
            (
                upload_id,
                e["person_id"],
                e["machine_type"],
                e["severity"],
                e["distance_norm"],
            )
            for e in events
        ]

        sql = """
            INSERT INTO proximity_events (
                upload_id,
                person_id,
                machine_type,
                severity,
                distance_norm
            )
            VALUES %s
        """

        with self.conn.cursor() as cur:
            execute_values(cur, sql, rows)

        self.conn.commit()

    def fetch(self, start_time, end_time) -> List[Dict]:
        """
        Fetch proximity events within a time range.
        """
        query = """
            SELECT * FROM proximity_events
            WHERE event_time >= %s AND event_time <= %s
            ORDER BY event_time ASC
        """
        try:
            # Need RealDictCursor or similar to return dicts with column names
            from psycopg2.extras import RealDictCursor
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (start_time, end_time))
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            # logging? assuming basic logging or print
            print(f"Failed to fetch proximity events: {e}") 
            return []
