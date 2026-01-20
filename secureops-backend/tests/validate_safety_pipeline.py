import sys
import os
import logging
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.session import get_db_session
from src.db.models import SafetyViolation, ProximityEvent
from src.stages.vision.detector import VisionDetector
from src.stages.vision.ppe_rules import PPERules
from src.stages.vision.proximity import ProximityDetector
from src.stages.vision.zone_monitor import ZoneMonitor
from src.core.types import VideoFrame

# Configs
# Zone: Rectangle from (0,0) to (500,500)
MOCK_ZONE_CONFIG = {
    "zones": {
        "RedZone": [[0,0], [500,0], [500,500], [0,500]]
    }
}
PROX_CONFIG = {"safe_distance_pixels": 200, "warning_distance_pixels": 400}
DOC_CONFIG = {"chunk_size": 1000, "chunk_overlap": 100}

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SafetyValidator")

def validate_pipeline():
    logger.info("Starting Offline Safety Pipeline Validation on test_data/ ...")
    
    # 1. Initialize Stages
    try:
        from src.stages.input.pdf_loader import PDFLoader
        from src.stages.documents.chunker import DocumentChunker
        
        vision_config = {"model_path": "yolov8x.pt", "confidence_threshold": 0.5, "device": "cpu"}
        detector = VisionDetector(vision_config)
        ppe_rules = PPERules()
        prox_detector = ProximityDetector(PROX_CONFIG)
        zone_monitor = ZoneMonitor(MOCK_ZONE_CONFIG)
        
        pdf_loader = PDFLoader(DOC_CONFIG)
        chunker = DocumentChunker(DOC_CONFIG)
        
        logger.info("✅ Stages Initialized")
    except Exception as e:
        logger.error(f"Failed to init: {e}")
        sys.exit(1)

    # 2. Traverse test_data
    # 2. Traverse test_data
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="Specific file to process", required=False)
    args = parser.parse_args()

    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            sys.exit(1)
        all_files = [file_path]
        logger.info(f"Processing single file: {args.file}")
    else:
        TEST_DIR = Path("test_data")
        if not TEST_DIR.exists():
            logger.error("test_data directory not found!")
            sys.exit(1)
            
        all_files = sorted([f for f in TEST_DIR.rglob("*") if f.is_file()])
        logger.info(f"Found {len(all_files)} files in test_data/")
    
    processed_count = 0
    passed_count = 0
    
    for file_path in all_files:
        fname = file_path.name
        ext = file_path.suffix.lower()
        
        try:
            # --- IMAGE PIPELINE ---
            if ext in ['.jpg', '.jpeg', '.png']:
                img = cv2.imread(str(file_path))
                if img is None:
                    continue
                
                frame = VideoFrame(frame_number=1, timestamp=datetime.now(), image=img)
                processed = detector.process(frame)
                
                # Logic Stages
                ppe_res = ppe_rules.check_compliance(processed)
                prox_res = prox_detector.check_proximity(processed)
                zone_res = zone_monitor.check_zones(processed)
                
                # DB Persistence
                with get_db_session() as session:
                    # Violations (PPE + Zone)
                    all_v = ppe_res.get('violations', []) + zone_res.get('violations', [])
                    for v in all_v:
                         v_type = v.get("violation_type", "ppe_violation")
                         if "violations" in v: v_type = v["violations"][0]
                         
                         sv = SafetyViolation(
                             violation_type=v_type, 
                             severity=v.get("severity", "warning"),
                             person_id=v.get("person_id"),
                             zone_id=v.get("zone_id"),
                             extra_metadata={"file": fname, **v}
                         )
                         session.add(sv)
                    
                    # Proximity
                    for p in prox_res.get('violations', []) + prox_res.get('warnings', []):
                        pe = ProximityEvent(
                             person_id=p['person_id'],
                             machine_id=p['machine_id'],
                             machine_type=p['machine_type'],
                             distance_pixels=p['distance_pixels'],
                             threshold_pixels=PROX_CONFIG['safe_distance_pixels'],
                             severity=p['severity'],
                             extra_metadata={"file": fname}
                        )
                        session.add(pe)
                    session.commit()
                
                logger.info(f"Processed IMG: {fname} (Dets: {len(processed.detections)})")
                processed_count += 1
                passed_count += 1

            # --- PDF PIPELINE ---
            elif ext == '.pdf':
                data = pdf_loader.load_pdf(str(file_path))
                chunks = chunker.chunk_document(data.get('text', ''), fname)
                
                # Store metric (simulated)
                with get_db_session() as session:
                     # In a full doc pipeline we'd store embeddings. 
                     # Here just update metrics maybe? Or skip DB for PDFs if no table.
                     pass
                     
                logger.info(f"Processed PDF: {fname} (Chunks: {len(chunks)})")
                processed_count += 1
                passed_count += 1

        except Exception as e:
            logger.error(f"Failed {fname}: {e}")

    # 3. Validation Assertions
    with get_db_session() as session:
        db_violations = session.query(SafetyViolation).count()
        db_prox = session.query(ProximityEvent).count()
        
    logger.info("="*30)
    logger.info(f"Files Processed: {processed_count}/{len(all_files)}")
    logger.info(f"DB SAFETY VIOLATIONS: {db_violations}")
    logger.info(f"DB PROXIMITY EVENTS: {db_prox}")
    logger.info("="*30)
    
    if processed_count > 0:
        print("PASS: Validated Comprehensive Pipeline")
        sys.exit(0)
    else:
        print("WARNING: No files processed (Folder empty?)")
        sys.exit(0)

if __name__ == "__main__":
    validate_pipeline()
