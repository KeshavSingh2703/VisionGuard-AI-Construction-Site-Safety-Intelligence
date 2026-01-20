import logging
import cv2
from datetime import datetime
import uuid
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.session import get_engine
from src.db.ppe_persistence import PPEViolationRepository
from src.db.repositories.proximity_repository import ProximityEventRepository
from src.db.repositories.zone_repository import ZoneEventRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PipelineSim")

def simulate():
    engine = get_engine()
    conn = engine.raw_connection()
    
    ppe_repo = PPEViolationRepository(conn)
    prox_repo = ProximityEventRepository(conn)
    zone_repo = ZoneEventRepository(conn)
    
    upload_id = str(uuid.uuid4())
    logger.info(f"Simulating pipeline run. Upload ID: {upload_id}")
    
    # 1. Simulate PPE Violations
    # 3 mock violations
    logger.info("Injecting PPE Violations...")
    for i in range(3):
        v = {
            "track_id": 100 + i,
            "source_id": upload_id,
            "violation_type": "PPE",
            "missing_items": ["helmet"] if i % 2 == 0 else ["vest", "helmet"],
            "severity": "HIGH",
            "start_time": datetime.now(),
            "end_time": datetime.now(), # Duration 0 for instantaneous sim
            "duration_seconds": 5.0,
            "confidence": 0.95
        }
        ppe_repo.save_violation(v)
        
    # 2. Simulate Proximity Events
    logger.info("Injecting Proximity Events...")
    prox_events = []
    for i in range(2):
        prox_events.append({
            "person_id": 200 + i,
            "machine_type": "excavator",
            "severity": "CRITICAL",
            "distance_norm": 0.05
        })
    prox_repo.save_events(upload_id, prox_events)
    
    # 3. Simulate Zone Events
    logger.info("Injecting Zone Events...")
    zone_events = []
    for i in range(4):
        zone_events.append({
            "object_id": 300 + i,
            "object_type": "person",
            "zone_id": "zone_A",
            "timestamp": datetime.now()
        })
    zone_repo.save_events(upload_id, zone_events)
    
    conn.close()
    logger.info("Simulation complete. Data populated.")

if __name__ == "__main__":
    simulate()
