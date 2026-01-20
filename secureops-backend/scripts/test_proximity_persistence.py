import logging
import uuid
import time
from src.db.session import get_engine
from src.db.repositories.proximity_repository import ProximityEventRepository

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_persistence():
    try:
        engine = get_engine()
        conn = engine.raw_connection()
        repo = ProximityEventRepository(conn)
        
        # Create Dummy Events
        upload_id = str(uuid.uuid4())
        events = [
            {
                "person_id": 101,
                "machine_type": "excavator",
                "severity": "WARNING",
                "distance_norm": 0.12,
                "timestamp": time.time()
            },
            {
                "person_id": 102,
                "machine_type": "dump_truck",
                "severity": "CRITICAL",
                "distance_norm": 0.05,
                "timestamp": time.time()
            }
        ]
        
        logger.info(f"Saving {len(events)} events for upload_id {upload_id}")
        repo.save_events(upload_id, events)
        
        # Verify
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM proximity_events WHERE upload_id = %s", (upload_id,))
            rows = cur.fetchall()
            
        conn.close()
        
        if len(rows) == 2:
            logger.info("✅ Verified: 2 events found in DB.")
            for r in rows:
                logger.info(f"  -> Row: {r}")
        else:
            logger.error(f"❌ Verification Failed: Expected 2 rows, found {len(rows)}")
            exit(1)
            
    except Exception as e:
        logger.error(f"Test Failed: {e}")
        exit(1)

if __name__ == "__main__":
    test_persistence()
