import psycopg2
import logging
import os

# Database code relies on .env or hardcoded?
# Checking src/db/session.py might be better but let's stick to simple psycopg2 if we know creds.
# Or better, reuse src/db/session logic if possible.
# Let's try to assume env vars are set or use the existing config way.
# Since I don't want to parse .env manually here if I can avoid it, let's use the same connection logic as seed_db.py or similar.
# Ah, I should use src.db.session.get_engine or similar.
# But let's look at how test_db_connection.py did it.

from src.db.session import get_engine

def apply_schema():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # SQL to create table
    sql = """
    DROP TABLE IF EXISTS proximity_events CASCADE;
    
    CREATE TABLE IF NOT EXISTS proximity_events (
        id BIGSERIAL PRIMARY KEY,
        upload_id UUID,
        person_id INTEGER NOT NULL,
        machine_type TEXT NOT NULL CHECK (
            machine_type IN ('excavator', 'dump_truck')
        ),
        severity TEXT NOT NULL CHECK (
            severity IN ('WARNING', 'CRITICAL')
        ),
        distance_norm REAL NOT NULL CHECK (distance_norm >= 0 AND distance_norm <= 1),
        event_time TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_proximity_upload_id
        ON proximity_events (upload_id);

    CREATE INDEX IF NOT EXISTS idx_proximity_severity
        ON proximity_events (severity);

    CREATE INDEX IF NOT EXISTS idx_proximity_event_time
        ON proximity_events (event_time);

    CREATE INDEX IF NOT EXISTS idx_proximity_person
        ON proximity_events (person_id);
    """
    
    try:
        engine = get_engine()
        conn = engine.raw_connection()
        with conn.cursor() as cur:
            cur.execute(sql)
            logger.info("Executed CREATE TABLE.")
        conn.commit()
        conn.close()
        logger.info("Schema applied successfully.")
        
    except Exception as e:
        logger.error(f"Failed to apply schema: {e}")

if __name__ == "__main__":
    apply_schema()
