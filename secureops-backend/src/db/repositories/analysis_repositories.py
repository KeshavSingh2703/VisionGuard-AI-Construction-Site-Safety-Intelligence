from typing import List, Dict, Any
from sqlalchemy.orm import Session
from src.db.models import SafetyViolation, ProximityEvent

class PPERepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_upload_id(self, upload_id: str) -> List[Dict[str, Any]]:
        """Fetch PPE violations for an upload."""
        # Filter where violation_type is NOT 'zone_intrusion' (assuming SafetyViolation holds both)
        # OR check specific types like 'NO_HELMET', 'NO_VEST', etc.
        # Based on models.py, SafetyViolation has 'violation_type'.
        # Previous code used 'missing_helmet' etc in 'violation_type' or 'description'.
        # Let's check Orchestrator persistence...
        # It saves: violation_type=v["violation_type"] (e.g. 'PPE_VIOLATION'?) and severity.
        # And Zone saves violation_type="zone_intrusion".
        
        entities = self.session.query(SafetyViolation).filter(
            SafetyViolation.upload_id == upload_id,
            SafetyViolation.violation_type != 'zone_intrusion'
        ).all()
        
        results = []
        for e in entities:
             # Convert to dict format expected by Aggregator
             results.append({
                 'timestamp': e.detected_at.timestamp(),
                 'person_id': e.extra_metadata.get('track_id') if e.extra_metadata else None,
                 'missing_helmet': 'helmet' in e.description.lower(), # Heuristic or from metadata
                 'missing_vest': 'vest' in e.description.lower(),
                 'frame_path': None, # Not currently stored?
                 'severity': e.severity,
                 'frame_number': e.frame_number
             })
        return results

class ZoneRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_upload_id(self, upload_id: str) -> List[Dict[str, Any]]:
        entities = self.session.query(SafetyViolation).filter(
            SafetyViolation.upload_id == upload_id,
            SafetyViolation.violation_type == 'zone_intrusion'
        ).all()
        
        results = []
        for e in entities:
            results.append({
                'timestamp': e.detected_at.timestamp(),
                'object_id': e.extra_metadata.get('object_id') if e.extra_metadata else None,
                'zone_id': e.extra_metadata.get('zone_id') if e.extra_metadata else None,
                'severity': e.severity,
                'frame_number': e.frame_number
            })
        return results

class ProximityRepository:
    def __init__(self, session: Session):
        self.session = session
        
    def get_events(self, upload_id: str) -> List[Dict[str, Any]]:
        entities = self.session.query(ProximityEvent).filter(
            ProximityEvent.upload_id == upload_id
        ).all()
        
        results = []
        for e in entities:
            results.append({
                'timestamp': e.detected_at.timestamp(),
                'person_id': e.worker_id,
                'machine_type': e.machine_type,
                'severity': e.risk_level,
                'distance_norm': e.distance_px, # Storing px as norm? Orchestrator model says distance_px.
                # Aggregator expected distance_norm.
                # In Orchestrator: distance_px=p.distance_norm * image_diag
                # We can return distance_px or try to normalize if we have image dims.
                # Let's return what we have.
                'frame_number': e.frame_number
            })
        return results
