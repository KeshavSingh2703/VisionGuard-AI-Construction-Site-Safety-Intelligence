import logging
import psycopg2
from src.db.session import get_engine

def apply_schema():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    sql = """
    DROP TABLE IF EXISTS ppe_violations CASCADE;

    CREATE TABLE IF NOT EXISTS ppe_violations (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

        -- Tracking
        track_id INTEGER NOT NULL,
        source_id UUID,                 -- video_id / upload_id (nullable for offline)

        -- Violation metadata
        violation_type TEXT NOT NULL CHECK (violation_type = 'PPE'),
        missing_items TEXT[] NOT NULL,  -- ['helmet'], ['vest'], ['helmet','vest']

        severity TEXT NOT NULL CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH')),

        -- Timing
        start_time TIMESTAMPTZ NOT NULL,
        end_time   TIMESTAMPTZ NOT NULL,
        duration_seconds REAL NOT NULL,

        -- Confidence
        confidence REAL NOT NULL CHECK (confidence >= 0 AND confidence <= 1),

        -- Audit
        created_at TIMESTAMPTZ DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_ppe_track_id ON ppe_violations(track_id);
    CREATE INDEX IF NOT EXISTS idx_ppe_severity ON ppe_violations(severity);
    CREATE INDEX IF NOT EXISTS idx_ppe_time ON ppe_violations(start_time, end_time);
    """
    
    try:
        engine = get_engine()
        conn = engine.raw_connection()
        with conn.cursor() as cur:
            cur.execute(sql)
            logger.info("Executed CREATE TABLE ppe_violations.")
        conn.commit()
        conn.close()
        logger.info("Schema applied successfully.")
        
    except Exception as e:
        logger.error(f"Failed to apply schema: {e}")

if __name__ == "__main__":
    apply_schema()
