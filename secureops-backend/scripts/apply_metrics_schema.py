import logging
import psycopg2
from src.db.session import get_engine

def apply_schema():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    sql = """
    DROP TABLE IF EXISTS site_metrics CASCADE;

    CREATE TABLE IF NOT EXISTS site_metrics (
        id SERIAL PRIMARY KEY,
        date DATE NOT NULL UNIQUE,

        total_violations INTEGER NOT NULL,
        low_count INTEGER NOT NULL,
        medium_count INTEGER NOT NULL,
        high_count INTEGER NOT NULL,
        critical_count INTEGER NOT NULL,

        compliance_rate FLOAT NOT NULL CHECK (compliance_rate >= 0 AND compliance_rate <= 1),
        risk_score FLOAT NOT NULL CHECK (risk_score >= 0 AND risk_score <= 100),

        created_at TIMESTAMP DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_site_metrics_date ON site_metrics(date);
    """
    
    try:
        engine = get_engine()
        conn = engine.raw_connection()
        with conn.cursor() as cur:
            cur.execute(sql)
            logger.info("Executed CREATE TABLE site_metrics.")
        conn.commit()
        conn.close()
        logger.info("Schema applied successfully.")
        
    except Exception as e:
        logger.error(f"Failed to apply schema: {e}")

if __name__ == "__main__":
    apply_schema()
