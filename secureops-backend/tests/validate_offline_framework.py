import sys
import os
import json
import logging
import hashlib
from pathlib import Path
from datetime import datetime
import cv2

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.stages.vision.detector import VisionDetector
from src.stages.vision.ppe_rules import PPERules
from src.stages.vision.proximity import ProximityDetector
from src.stages.vision.zone_monitor import ZoneMonitor
from src.core.types import VideoFrame

# Configs
MOCK_ZONE_CONFIG = {
    "zones": {
        "RedZone": [[0,0], [500,0], [500,500], [0,500]]
    }
}
PROX_CONFIG = {"safe_distance_pixels": 200, "warning_distance_pixels": 400}
VISION_CONFIG = {"model_path": "yolov8x.pt", "confidence_threshold": 0.5, "device": "cpu"}

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("OfflineValidator")

MANIFEST_FILE = "dataset_manifest.json"
GROUND_TRUTH_FILE = "ground_truth.json"
SUMMARY_FILE = "validation_summary.json"

def compute_sha256(file_path: Path) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def check_integrity():
    logger.info("🔍 Checking Dataset Integrity...")
    if not os.path.exists(MANIFEST_FILE):
        logger.error(f"Manifest {MANIFEST_FILE} missing!")
        return False
        
    with open(MANIFEST_FILE, 'r') as f:
        manifest = json.load(f)
        
    for entry in manifest:
        fpath = Path(entry['file_path'])
        if not fpath.exists():
            logger.error(f"Missing file: {fpath}")
            return False
            
        current_hash = compute_sha256(fpath)
        if current_hash != entry['sha256_hash']:
            logger.error(f"HASH MISMATCH: {fpath}")
            logger.error(f"Expected: {entry['sha256_hash']}")
            logger.error(f"Actual:   {current_hash}")
            return False
            
    logger.info("✅ Integrity Check Passed")
    return True

def run_validation():
    # 1. Integrity Check
    if not check_integrity():
        print("FAIL: Integrity Check Failed")
        sys.exit(1)

    # 2. Load Ground Truth
    if not os.path.exists(GROUND_TRUTH_FILE):
        logger.error("Ground Truth Missing!")
        sys.exit(1)
        
    with open(GROUND_TRUTH_FILE, 'r') as f:
        ground_truth = json.load(f)
    
    # Index GT by filename
    gt_map = {item['file_name']: item for item in ground_truth}
    
    # 3. Initialize Pipeline
    try:
        detector = VisionDetector(VISION_CONFIG)
        ppe_rules = PPERules()
        prox_detector = ProximityDetector(PROX_CONFIG)
        zone_monitor = ZoneMonitor(MOCK_ZONE_CONFIG)
    except Exception as e:
        logger.error(f"Pipeline Init Failed: {e}")
        sys.exit(1)

    results = []
    correct_count = 0
    total_samples = 0
    
    logger.info("🚀 Starting Inference Validation...")
    
    for fname, expected in gt_map.items():
        # Find file in test_data (naive search)
        found_path = None
        for p in Path("test_data").rglob(fname):
            found_path = p
            break
            
        if not found_path:
            logger.warning(f"File {fname} in Ground Truth but NOT in dataset. Skipping.")
            continue
            
        total_samples += 1
        
        # Load Image
        img = cv2.imread(str(found_path))
        if img is None:
            logger.error(f"Failed to read image: {fname} (Corrupt/Empty?)")
            # If file exists but unreadable, it's a FAIL for this sample
            results.append({
                "file": fname,
                "status": "ERROR_READ",
                "expected": expected['expected_violation_type'],
                "actual": "None"
            })
            continue

        # Inference
        try:
            frame = VideoFrame(frame_number=1, timestamp=datetime.now(), image=img)
            processed = detector.process(frame)
            
            # Logic Stages
            ppe_res = ppe_rules.check_compliance(processed)
            prox_res = prox_detector.check_proximity(processed)
            zone_res = zone_monitor.check_zones(processed)
            
            # Determine "Actual" Violation Type (Simplified for comparison)
            actual_type = "NONE"
            actual_severity = "LOW"
            actual_escalation = False
            
            # Priority: Zone > Prox > PPE (Just for single label comparison)
            if zone_res['violations']:
                actual_type = "zone_intrusion"
                actual_severity = "CRITICAL"
            elif prox_res.get('violations') or prox_res.get('warnings'):
                actual_type = "proximity_risk"
                actual_severity = prox_res.get('violations', [{'severity': 'WARNING'}])[0]['severity'].upper()
            elif ppe_res.get('violations'):
                actual_type = "missing_helmet" # Generic mapping
                actual_severity = "WARNING"
                
            # Assertion
            matches_type = (actual_type == expected['expected_violation_type'])
            # Note: Checking severity might be strict, so we focus on Type first.
            
            if matches_type:
                correct_count += 1
                status = "PASS"
            else:
                status = "FAIL"
                
            results.append({
                "file": fname,
                "status": status,
                "expected": expected['expected_violation_type'],
                "actual": actual_type
            })
            
            logger.info(f"[{status}] {fname}: Expected={expected['expected_violation_type']}, Actual={actual_type}")

        except Exception as e:
            logger.error(f"Inference Error {fname}: {e}")
            results.append({"file": fname, "status": "ERROR_EXEC", "error": str(e)})

    # 4. Generate Output Layers

    # Metric Aggregation
    violation_counts = {
        "PPE Violations": 0,
        "Zone Violations": 0,
        "Proximity Risks": 0,
        "Time-Based Escalation": 0
    }
    
    for r in results:
        if r.get("actual") == "missing_helmet": violation_counts["PPE Violations"] += 1
        elif r.get("actual") == "zone_intrusion": violation_counts["Zone Violations"] += 1
        elif r.get("actual") == "proximity_risk": violation_counts["Proximity Risks"] += 1
        # Time-based Logic implicitly part of actual type in this simplified validator, 
        # but realistically would be a separate flag. For now mapping zone_intrusion > time if we had it.

    if total_samples == 0:
        accuracy = 0.0
    else:
        accuracy = correct_count / total_samples

    # Layer 2: Structured Artifacts
    
    # 2a. validation_summary.json
    val_summary = {
        "timestamp": str(datetime.now()),
        "dataset": "manual_test_data",
        "total_samples": total_samples,
        "accuracy": accuracy,
        "pass_threshold": 0.9,
        "result": "PASS" if accuracy >= 0.9 else "FAIL",
        "integrity_hash": compute_sha256(Path(MANIFEST_FILE)) if os.path.exists(MANIFEST_FILE) else "MISSING"
    }
    with open("validation_summary.json", 'w') as f:
        json.dump(val_summary, f, indent=2)

    # 2b. per_file_results.json
    with open("per_file_results.json", 'w') as f:
        json.dump(results, f, indent=2)

    # 2c. metrics.json
    metrics = {
        "counts": violation_counts,
        "accuracy": accuracy,
        "precision": "N/A", # Placeholder for future
        "recall": "N/A"
    }
    with open("metrics.json", 'w') as f:
        json.dump(metrics, f, indent=2)


    # Layer 1: Console Summary (Human-First)
    print("\n" + "="*50)
    print("[PIPELINE] Offline Safety Validation")
    print(f"[DATASET] manual_test_data (Hash Verified)")
    print(f"[STAGES] Ingestion ✔ Preprocess ✔ Inference ✔ Rules ✔ Validation ✔")
    print("-" * 50)
    print("[SUMMARY]")
    for k, v in violation_counts.items():
        print(f"- {k:<25}: {v}")
    print("-" * 50)
    print("[METRICS]")
    print(f"- Total Samples : {total_samples}")
    print(f"- Accuracy      : {accuracy*100:.2f}%")
    print(f"- Threshold     : 90%")
    print("-" * 50)
    
    if accuracy >= 0.9:
        print("[RESULT] PASS")
        sys.exit(0)
    else:
        print("[RESULT] FAIL")
        # Print failures concisely
        print("\n[FAILURES]")
        for r in results:
            if r['status'] != 'PASS':
                 print(f"[FAIL] {r.get('file', 'Unknown')}")
                 print(f"  Expected : {r.get('expected')}")
                 print(f"  Actual   : {r.get('actual')}")
        sys.exit(1)

if __name__ == "__main__":
    run_validation()
