from src.db.session import get_db_session
from src.db.models import Upload, SiteMetrics, SafetyViolation
import sys

def inspect():
    with get_db_session() as session:
        print("\n--- Recent Uploads ---")
        uploads = session.query(Upload).order_by(Upload.created_at.desc()).limit(5).all()
        for u in uploads:
            print(f"ID: {u.id} | Type: {u.upload_type} | Status: {u.status} | File: {u.original_filename}")
            
            # Check metrics
            m = session.query(SiteMetrics).filter(SiteMetrics.upload_id == u.id).first()
            if m:
                print(f"  > Metrics: Accuracy={m.accuracy}%, PPE={m.ppe_violations}, Zone={m.zone_violations}, Pipeline Status={m.pipeline_status}")
            else:
                print(f"  > Metrics: NONE (Pipeline hasn't saved metrics yet)")
                
            # Check violations count
            v_count = session.query(SafetyViolation).filter(SafetyViolation.upload_id == u.id).count()
            print(f"  > Saved Violations: {v_count}")
            print("-" * 30)

if __name__ == "__main__":
    inspect()
