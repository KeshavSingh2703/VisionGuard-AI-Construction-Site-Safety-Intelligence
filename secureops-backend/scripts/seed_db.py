import uuid
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.session import init_db, get_db_session
from src.db import models

def seed():
    print("Initializing Database...")
    # Explicitly drop all to ensure clean slate for authoritative schema
    from src.db.session import drop_db, init_db
    
    print("Dropping old tables...")
    drop_db()
    
    print("Creating new tables...")
    init_db()
    
    print("Seeding Data...")
    with get_db_session() as session:
        upload_id = str(uuid.uuid4())
        
        # 1. Upload Record
        print(f"Creating Upload: {upload_id}")
        session.add(models.Upload(
            id=upload_id,
            upload_type="image",
            original_filename="test_batch.zip",
            stored_path="data/uploads/test",
            status="completed"
        ))
        
        # 2. Site Metrics
        session.add(models.SiteMetrics(
            id=uuid.uuid4(),
            upload_id=upload_id,
            total_files=10,
            accuracy=92.3,
            ppe_violations=3,
            zone_violations=1,
            proximity_violations=2,
            time_based_violations=1,
            pipeline_status="PASS"
        ))
        
        # 3. Safety Violations
        session.add(models.SafetyViolation(
            id=uuid.uuid4(),
            upload_id=upload_id,
            file_name="img_001.jpg",
            violation_type="PPE",
            severity="HIGH",
            confidence=0.91,
            description="Missing Helmet"
        ))
        
        session.add(models.SafetyViolation(
            id=uuid.uuid4(),
            upload_id=upload_id,
            file_name="img_002.jpg",
            violation_type="ZONE",
            severity="CRITICAL",
            confidence=0.95,
            description="Entered Red Zone"
        ))
        
        # 4. Proximity Events
        session.add(models.ProximityEvent(
            id=uuid.uuid4(),
            upload_id=upload_id,
            file_name="img_003.jpg",
            worker_id="w_123",
            machine_type="Excavator",
            distance_px=45.5,
            risk_level="HIGH"
        ))

        session.commit()
        print("✅ Database Seeded Successfully!")

if __name__ == "__main__":
    seed()
