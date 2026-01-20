"""PPE Rule Engine for deterministic safety compliance."""

import logging
import time
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from src.core.types import VideoFrame, Detection
from src.utils.image_quality import ImageQualityChecker

logger = logging.getLogger(__name__)

class PPERuleEngine:
    """
    Enforces PPE safety rules with Strict Temporal Persistence (Phase 4).
    Replaces weighted voting with frame-counting logic to eliminate flickering.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.min_confidence = self.config.get("min_confidence", 0.5)
        self.smoothing_window = self.config.get("smoothing_window", 2.0)
        self.compliance_buffer = self.config.get("compliance_buffer", 1.0)
        
        # Quality Gate
        self.quality_checker = ImageQualityChecker()
        
        # State Tracking
        # Structure:
        # {
        #   track_id: {
        #       "helmet": {
        #           "missing_count": 0, "present_count": 0,
        #           "active_violation": bool, "violation_start": float, "last_conf": float
        #       },
        #       "vest": { ... },
        #       "violation_history": [],
        #       "last_update": float
        #   }
        # }
        self.track_states: Dict[int, Dict[str, Any]] = {}

        # Cleanup
        self.last_cleanup = time.time()
        self.cleanup_interval = 60.0
        self.stale_threshold = 30.0

    def reset(self):
        self.track_states.clear()
        self.last_cleanup = time.time()
        
    def check_compliance(self, frame: VideoFrame, quality_score: float = 1.0) -> List[Dict[str, Any]]:
        current_time = frame.timestamp.timestamp()
        
        # 1. Quality Gate
        # Use passed score or checker? Using passed score is better if available.
        # But we still run checker if quality_score is default 1.0 maybe?
        # For now, we trust the inputs.
        
        generated_events = []

        # 2. Group detections
        person_map = {}
        for det in frame.detections:
            if det.confidence < self.min_confidence: continue
            track_id = det.metadata.get("track_id")
            if track_id is None: continue
            
            track_id = int(track_id)
            if track_id not in person_map:
                person_map[track_id] = {"items": [], "person_det": None}
            
            if det.class_name == "person":
                person_map[track_id]["person_det"] = det
            else:
                person_map[track_id]["items"].append(det)

        # 3. Update State & Check Rules
        all_track_ids = set(self.track_states.keys()) | set(person_map.keys())
        
        for track_id in all_track_ids:
            # Initialize state if new
            if track_id not in self.track_states:
                self.track_states[track_id] = {
                    "helmet": {
                        "missing_count": 0, 
                        "present_count": 0, 
                        "active_violation": False, 
                        "violation_start": None,
                        "unknown_start": None,
                        "last_conf": 0.0
                    },
                    "vest": {
                        "missing_count": 0, 
                        "present_count": 0, 
                        "active_violation": False, 
                        "violation_start": None,
                        "unknown_start": None,
                        "last_conf": 0.0
                    },
                    "violation_history": [],
                    "last_update": current_time
                }
            
            data = person_map.get(track_id)
            
            # Update State (Only if we have fresh data data)
            if data:
                self.track_states[track_id]["last_update"] = current_time
                items = data["items"]
                
                # --- HELMET ---
                has_helmet = any(d.class_name == "helmet" for d in items)
                has_no_helmet = any(d.class_name == "no_helmet" for d in items)
                
                is_viol = None
                h_conf = 0.5
                if has_no_helmet: 
                    is_viol = True
                    dets = [d for d in items if d.class_name == "no_helmet"]
                    h_conf = max(d.confidence for d in dets) if dets else 0.5
                elif has_helmet: 
                    is_viol = False
                    dets = [d for d in items if d.class_name == "helmet"]
                    h_conf = max(d.confidence for d in dets) if dets else 0.5
                # Else None (Unknown)

                self._update_state(track_id, "helmet", is_viol, h_conf, current_time)

                # --- VEST ---
                has_vest = any(d.class_name in ["vest", "safety_vest"] for d in items)
                has_no_vest = any(d.class_name == "no_vest" for d in items)
                
                is_viol = None
                v_conf = 0.5
                if has_no_vest: 
                    is_viol = True
                    dets = [d for d in items if d.class_name == "no_vest"]
                    v_conf = max(d.confidence for d in dets) if dets else 0.5
                elif has_vest: 
                    is_viol = False
                    dets = [d for d in items if d.class_name in ["vest", "safety_vest"]]
                    v_conf = max(d.confidence for d in dets) if dets else 0.5
                
                self._update_state(track_id, "vest", is_viol, v_conf, current_time)

            # Check Stale
            if current_time - self.track_states[track_id]["last_update"] > self.stale_threshold:
                continue

            # Evaluate Voting (Now checking flags)
            helmet_viol = self.track_states[track_id]["helmet"]["active_violation"]
            vest_viol = self.track_states[track_id]["vest"]["active_violation"]

            # Construct Event
            missing_items = []
            confs = []
            
            if helmet_viol:
                missing_items.append("helmet")
                confs.append(self.track_states[track_id]["helmet"]["last_conf"])
            
            if vest_viol:
                missing_items.append("vest")
                confs.append(self.track_states[track_id]["vest"]["last_conf"])
                
            if missing_items:
                severity, _ = self._calculate_severity(track_id, current_time, missing_items)
                final_conf = max(confs) if confs else 0.5
                
                # Get bbox from current person detection if available
                person_det = data.get("person_det") if data else None
                bbox = person_det.bbox if person_det else None

                event = {
                    "violation_type": "PPE",
                    "missing_items": missing_items,
                    "severity": severity,
                    "confidence": final_conf,
                    "track_id": track_id,
                    "bbox": bbox,
                    "start_time": datetime.fromtimestamp(current_time).isoformat(),
                    "timestamp": datetime.fromtimestamp(current_time)
                }
                generated_events.append(event)
                
        # Cleanup
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup_states(current_time)
            
        return generated_events

    def _update_state(self, track_id, item, is_violation, confidence, now):
        """
        Phase 4: Strict Temporal Logic.
        Replaces Weighted Voting with counter-based persistence.
        Phase 6: Unknown Escalation.
        """
        state = self.track_states[track_id][item]
        state["last_conf"] = confidence
        
        # Configuration
        START_THRESHOLD = 3   # Frames to trigger violation (Lowered from 10 to catch faster violations)
        END_THRESHOLD = 1     # Frames to clear violation (Lowered from 3)
        UNKNOWN_TIMEOUT = 5.0 # Seconds to escalate Unknown -> Missing
        
        if is_violation is True:
            # Increment missing, reset present
            state["missing_count"] += 1
            state["present_count"] = 0
            state["unknown_start"] = None
        elif is_violation is False:
            # Increment present, reset missing
            state["present_count"] += 1
            state["missing_count"] = 0
            state["unknown_start"] = None
        else:
            # Unknown state
            # Start timer if not running
            if state.get("unknown_start") is None:
                state["unknown_start"] = now
            
            # Check Escalation
            if now - state["unknown_start"] > UNKNOWN_TIMEOUT:
                # Escalate: Treat as Missing
                state["missing_count"] += 1
                state["present_count"] = 0
            else:
                # Persistence: Hold counts steady
                pass
            
        # Logic Triggers
        if not state["active_violation"]:
            # Check for start
            if state["missing_count"] >= START_THRESHOLD:
                state["active_violation"] = True
                state["violation_start"] = now
        else:
            # Check for end
            if state["present_count"] >= END_THRESHOLD:
                state["active_violation"] = False
                state["violation_start"] = None

    def _calculate_severity(self, track_id: int, now: float, missing: List[str]) -> tuple[str, float]:
        """Determine severity LOW/MEDIUM/HIGH."""
        # Check max duration of current missing items
        max_duration = 0.0
        for item in missing:
            start = self.track_states[track_id][item]["violation_start"]
            if start:
                max_duration = max(max_duration, now - start)
        
        # History check for HIGH
        history = self.track_states[track_id]["violation_history"]
        
        # Prune history (10 min window)
        ten_mins_ago = now - 600
        history = [t for t in history if t > ten_mins_ago]
        self.track_states[track_id]["violation_history"] = history
        
        if len(history) >= 2: # 2 previous + current = 3
            return "HIGH", 1.0
            
        if max_duration >= 5.0:
            return "MEDIUM", 0.8
            
        return "LOW", 0.5
        
    def _cleanup_states(self, now: float):
        """Remove stale tracking data."""
        to_remove = []
        for track_id, state in self.track_states.items():
            if now - state["last_update"] > self.stale_threshold:
                to_remove.append(track_id)
        
        for tid in to_remove:
            del self.track_states[tid]
            
        self.last_cleanup = now
