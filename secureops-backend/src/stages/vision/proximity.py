import math
import time
from collections import defaultdict
from typing import List, Dict, Any, Optional


class ProximityEvent:
    def __init__(
        self,
        person_id: int,
        machine_type: str,
        severity: str,
        distance_norm: float,
        timestamp: float,
    ):
        self.person_id = person_id
        self.machine_type = machine_type
        self.severity = severity
        self.distance_norm = distance_norm
        self.timestamp = timestamp

    def to_dict(self):
        return {
            "person_id": self.person_id,
            "machine_type": self.machine_type,
            "severity": self.severity,
            "distance_norm": round(self.distance_norm, 4),
            "timestamp": self.timestamp,
        }


class ProximityDetector:
    """
    Detects worker–machine proximity using normalized centroid distance
    with temporal smoothing.
    """

    WARNING_THRESHOLD = 0.15
    CRITICAL_THRESHOLD = 0.08

    WARNING_TIME = 0.5   # seconds
    CRITICAL_TIME = 1.0  # seconds

    def __init__(self):
        # person_id -> state
        self.states = defaultdict(dict)

    @staticmethod
    def _centroid(box):
        x1, y1, x2, y2 = box
        return ((x1 + x2) / 2, (y1 + y2) / 2)

    @staticmethod
    def _euclidean(p1, p2):
        return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

    def reset(self):
        """Reset internal state."""
        self.states.clear()

    def process(
        self,
        persons: List[Dict[str, Any]],
        machines: List[Dict[str, Any]],
        image_width: int,
        image_height: int,
        now: Optional[float] = None,
    ) -> List[ProximityEvent]:
        """
        Process detections to find proximity violations.
        
        Args:
            persons: List of dicts with 'track_id' and 'bbox' [x1, y1, x2, y2]
            machines: List of dicts with 'label' and 'bbox' [x1, y1, x2, y2]
            image_width: Width of image
            image_height: Height of image
            now: Current timestamp (optional)
        """

        if now is None:
            now = time.time()

        image_diag = math.sqrt(image_width**2 + image_height**2)
        events: List[ProximityEvent] = []

        # Logic: For each person, find strictly the CLOSEST machine of relevant type.
        for person in persons:
            pid = person.get("track_id")
            if pid is None: continue # Skip untracked persons (optional constraint, but good for stability)

            p_centroid = self._centroid(person["bbox"])

            closest_machine = None
            closest_dist = float("inf")

            for machine in machines:
                if machine["label"] not in {"excavator", "dump_truck"}:
                    continue

                m_centroid = self._centroid(machine["bbox"])
                dist = self._euclidean(p_centroid, m_centroid)

                if dist < closest_dist:
                    closest_dist = dist
                    closest_machine = machine

            if not closest_machine:
                self.states.pop(pid, None)
                continue

            norm_dist = closest_dist / image_diag if image_diag > 0 else float('inf')
            state = self.states.get(pid)

            severity = None
            threshold_time = None

            if norm_dist < self.CRITICAL_THRESHOLD:
                severity = "CRITICAL"
                threshold_time = self.CRITICAL_TIME
            elif norm_dist < self.WARNING_THRESHOLD:
                severity = "WARNING"
                threshold_time = self.WARNING_TIME

            if severity is None:
                # Reset only if safe persists for a moment (hysteresis-like cleanup)
                # or strictly pop immediately if safe. 
                # The prompt logic suggested pop if safe persists >= 1.0s or immediately?
                # "Reset only if safe persists" -> checks state["last_seen"]
                if state and now - state["last_seen"] >= 1.0:
                    self.states.pop(pid, None)
                continue

            # Update State
            if not state or state["severity"] != severity:
                self.states[pid] = {
                    "severity": severity,
                    "start_time": now,
                    "last_seen": now,
                    "machine_type": closest_machine["label"],
                }
                continue

            state["last_seen"] = now
            duration = now - state["start_time"]

            if duration >= threshold_time:
                events.append(
                    ProximityEvent(
                        person_id=pid,
                        machine_type=state["machine_type"],
                        severity=severity,
                        distance_norm=norm_dist,
                        timestamp=now,
                    )
                )

        return events
