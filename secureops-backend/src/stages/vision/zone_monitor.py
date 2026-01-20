import time
from collections import defaultdict
from typing import List, Dict, Optional
import yaml
from shapely.geometry import Point, Polygon


class ZoneViolation:
    def __init__(self, object_id, object_type, zone_id, timestamp):
        self.object_id = object_id
        self.object_type = object_type
        self.zone_id = zone_id
        self.timestamp = timestamp

    def to_dict(self):
        return {
            "object_id": self.object_id,
            "object_type": self.object_type,
            "zone_id": self.zone_id,
            "timestamp": self.timestamp,
        }


class ZoneMonitor:
    MIN_DURATION = 1.0  # seconds

    def __init__(self):
        self.zones = {}
        # State tracking: state[object_id][zone_id] = start_timestamp
        self.state = defaultdict(dict)

    def load_zones(self, yaml_path: str):
        """Load zones from a YAML file."""
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)
        
        # Support both the auto-generated format (dict of filename->zones) 
        # and a simpler list format if we were to use one. 
        # The auto-label script created a dict: filename -> {name, points}.
        # But this monitor is likely running PER CAMERA/VIDEO.
        # For the validation dataset reuse, we need to be careful.
        # The user's reference code assumes `data["zones"]` list.
        # The auto-label script generated a dict keyed by filename.
        # ADAPTATION: To verify against the validation dataset (which has different zones per image),
        # we might need to load zones dynamically or pass the specific zone for the frame.
        # HOWEVER, for a PRODUCTION implementation, zones are valid for the whole camera stream.
        # Let's implement standard "List of Zones" loading as per user reference for production usage.
        # AND I will add a helper to "set_zones_for_image" for the verification script to use.
        
        if "zones" in data:
            for zone in data["zones"]:
                self.zones[zone["id"]] = Polygon(zone["polygon"])

    def set_zones(self, zones_dict: Dict[str, Polygon]):
        """Helper to manually set zones (e.g. for testing specific images)."""
        self.zones = zones_dict

    def _centroid(self, bbox):
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)

    def reset(self):
        """Reset internal state."""
        self.state.clear()

    def check_violations(
        self,
        detections: List[Dict],
        timestamp: Optional[float] = None,
    ) -> List[ZoneViolation]:
        """
        Check for violations.
        
        Args:
            detections: List of dicts with 'track_id', 'label', 'bbox'.
            timestamp: Current timestamp (defaults to time.time()).
            
        Returns:
            List of ZoneViolation objects.
        """

        if timestamp is None:
            timestamp = time.time()

        violations = []
        
        # Track which (obj, zone) pairs are active this frame to handle exits
        active_pairs = set()

        for det in detections:
            # Handle both 'track_id' (tracking) and 'object_id' (some formats) or 'id'
            obj_id = det.get("track_id", det.get("object_id", -1))
            obj_type = det.get("label", det.get("cls", "unknown"))
            
            # Skip invalid IDs if strict tracking needed, but for now allow -1 if just testing one frame
            
            centroid = self._centroid(det["bbox"])
            point = Point(centroid)

            for zone_id, polygon in self.zones.items():
                # CRITICAL: Use covers() for boundary safety
                inside = polygon.covers(point)
                
                if inside:
                    active_pairs.add((obj_id, zone_id))
                    start_time = self.state[obj_id].get(zone_id)

                    if start_time is None:
                        # Entered zone
                        self.state[obj_id][zone_id] = timestamp
                    elif timestamp - start_time >= self.MIN_DURATION:
                        # Violation confirmed
                        violations.append(
                            ZoneViolation(
                                object_id=obj_id,
                                object_type=obj_type,
                                zone_id=zone_id,
                                timestamp=timestamp,
                            )
                        )
                    # Else: still inside but waiting for timer

        # Cleanup state for objects that left zones
        # We need to look at all tracked objects in state
        # A robust way: 
        # If (obj, zone) is in state but NOT in active_pairs -> removed.
        # Note: This assumes 'detections' contains ALL objects currently visible.
        # If an object is lost by tracker, it naturally 'leaves' the zone here.
        
        keys_to_remove = []
        for obj_id, zone_map in self.state.items():
            for zone_id in list(zone_map.keys()):
                if (obj_id, zone_id) not in active_pairs:
                    keys_to_remove.append((obj_id, zone_id))
        
        for obj, z in keys_to_remove:
            self.state[obj].pop(z, None)
            
        return violations
