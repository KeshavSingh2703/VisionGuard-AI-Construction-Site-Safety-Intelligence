import logging
import psycopg2
from src.db.session import get_engine

def apply_schema():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    sql = """
    DROP TABLE IF EXISTS zone_events CASCADE;
    
    CREATE TABLE IF NOT EXISTS zone_events (
        id BIGSERIAL PRIMARY KEY,
        upload_id UUID NOT NULL,
        object_id INTEGER NOT NULL,
        object_type TEXT NOT NULL,
        zone_id TEXT NOT NULL,
        event_time TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_zone_upload_id ON zone_events (upload_id);
    CREATE INDEX IF NOT EXISTS idx_zone_object_id ON zone_events (object_id);
    CREATE INDEX IF NOT EXISTS idx_zone_zone_id ON zone_events (zone_id);
    CREATE INDEX IF NOT EXISTS idx_zone_time ON zone_events (event_time);
    """
    
    try:
        engine = get_engine()
        conn = engine.raw_connection()
        with conn.cursor() as cur:
            cur.execute(sql)
            logger.info("Executed CREATE TABLE zone_events.")
        conn.commit()
        conn.close()
        logger.info("Schema applied successfully.")
        
    except Exception as e:
        logger.error(f"Failed to apply schema: {e}")

if __name__ == "__main__":
    apply_schema()
