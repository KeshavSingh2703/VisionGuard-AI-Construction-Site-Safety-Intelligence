from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

@dataclass
class UnifiedViolation:
    """
    Normalized violation event for analytics and reporting.
    """
    timestamp: float
    violation_type: str  # 'ppe', 'proximity', 'zone'
    severity: str        # 'safe', 'warning', 'critical' (normalized)
    details: Dict[str, Any]
    image_path: Optional[str] = None
    
    @property
    def datetime(self) -> datetime:
        return datetime.fromtimestamp(self.timestamp)

class ViolationAggregator:
    """
    Aggregates violations from multiple streams (PPE, Proximity, Zone)
    into a unified format for analytics.
    """
    def __init__(self, ppe_repo, proximity_repo, zone_repo):
        self.ppe_repo = ppe_repo
        self.proximity_repo = proximity_repo
        self.zone_repo = zone_repo

    def get_unified_stream(self, upload_id: str) -> List[UnifiedViolation]:
        """Fetch and merge all violation types with Risk Escalation."""
        stream = []
        
        # 1. PPE Violations
        ppe_events = self.ppe_repo.get_by_upload_id(upload_id)
        for e in ppe_events:
            # Check ptype for severity baseline
            # Assuming 'violation_type' field in DB maps to 'PPE'
            base_severity = e.get('severity', 'warning').lower()
            
            stream.append(UnifiedViolation(
                timestamp=e.get('timestamp', 0),
                violation_type='ppe',
                severity=base_severity,
                details={
                    'track_id': e.get('track_id') or e.get('person_id'),
                    'missing_items': e.get('extra_metadata', {}).get('missing_items', []),
                    'escalated': False
                },
                image_path=e.get('image_path')
            ))

        # 2. Proximity Events
        prox_events = self.proximity_repo.get_events(upload_id)
        for e in prox_events:
            sev = e.get('severity', 'safe').lower()
            if sev == 'safe': continue 
            
            stream.append(UnifiedViolation(
                timestamp=e.get('timestamp', 0),
                violation_type='proximity',
                severity=sev,
                details={
                    'track_id': e.get('person_id'), # Normalized to track_id
                    'machine_type': e.get('machine_type'),
                    'distance': e.get('distance_norm'),
                    'escalated': False
                },
                image_path=e.get('image_path')
            ))

        # 3. Zone Events
        zone_events = self.zone_repo.get_by_upload_id(upload_id)
        for e in zone_events:
            stream.append(UnifiedViolation(
                timestamp=e.get('timestamp', 0),
                violation_type='zone',
                severity='critical',
                details={
                    'track_id': e.get('object_id'), # Normalized
                    'zone_id': e.get('zone_id'),
                    'escalated': False
                },
                image_path=e.get('image_path')
            ))
            
        # 4. Risk Escalation (Co-Occurrence)
        # Group by (track_id, rounded_timestamp)
        # We group events occurring within same 1-second window
        
        grouped = {}
        for event in stream:
            tid = event.details.get('track_id')
            if tid is None: continue
            
            # Key: TrackID + Timestamp (int)
            key = (int(tid), int(event.timestamp)) # 1s resolution
            if key not in grouped: grouped[key] = []
            grouped[key].append(event)
            
        for key, events in grouped.items():
            current_types = {x.violation_type for x in events}
            has_prox = 'proximity' in current_types
            has_zone = 'zone' in current_types
            
            # Filter for PPE events to apply logic
            ppe_events_in_group = [x for x in events if x.violation_type == 'ppe']
            
            for ppe_ev in ppe_events_in_group:
                missing = ppe_ev.details.get('missing_items', [])
                
                # CASE A: No Helmet + Risk -> CRITICAL
                if 'helmet' in missing:
                    if has_prox or has_zone:
                        ppe_ev.severity = 'critical'
                        ppe_ev.details['escalated'] = True
                        ppe_ev.details['escalation_reason'] = 'Helmet + Risk Zone'
                
                # CASE B & C: Vest Logic
                if 'vest' in missing:
                    if has_prox or has_zone:
                        # CASE B: Vest + Zone -> MEDIUM (Warning)
                        # Upgrade if currently low/safe
                        if ppe_ev.severity in ['safe', 'low']: 
                             ppe_ev.severity = 'warning'
                             ppe_ev.details['escalated'] = True
                             ppe_ev.details['escalation_reason'] = 'Vest + Risk Zone'
                    else:
                        # CASE C: Isolated Vest -> IGNORE (Safe)
                        # ONLY if Helmet is NOT present in missing list (Helmet is mandatory everywhere)
                        if 'helmet' not in missing:
                             ppe_ev.severity = 'safe'
                             ppe_ev.details['escalation_reason'] = 'Vest Ignored (Safe Zone)'
                             ppe_ev.details['ignored'] = True

        # Sort by timestamp
        stream.sort(key=lambda x: x.timestamp)
        return stream
