import pytest
import time
from shapely.geometry import Polygon
from src.stages.vision.zone_monitor import ZoneMonitor

def test_geometry_covers_boundary():
    """Test that boundary points are considered INSIDE using covers()."""
    monitor = ZoneMonitor()
    # 10x10 square at origin
    monitor.zones = {
        "test_zone": Polygon([(0,0), (10,0), (10,10), (0,10)])
    }
    
    # Point on boundary (0,0)
    # If covers() works, this is inside.
    # Note: ZoneMonitor._centroid takes bbox (x1, y1, x2, y2)
    
    # Boundary Point BBox (0, 0, 0, 0)
    dets = [{"track_id": 1, "label": "person", "bbox": (0, 0, 0, 0)}] 
    t0 = time.time()
    
    # First frame - entry (no violation yet due to timer)
    monitor.check_violations(dets, timestamp=t0)
    
    # Check state was set
    assert "test_zone" in monitor.state[1]
    assert monitor.state[1]["test_zone"] == t0
    
def test_temporal_smoothing():
    """Test violation triggers only after MIN_DURATION."""
    monitor = ZoneMonitor()
    monitor.zones = {
        "test_zone": Polygon([(0,0), (10,0), (10,10), (0,10)])
    }
    
    # Center point (5,5)
    dets = [{"track_id": 1, "label": "person", "bbox": (5, 5, 5, 5)}]
    
    t0 = 1000.0
    
    # T=0: Entry
    v = monitor.check_violations(dets, timestamp=t0)
    assert len(v) == 0
    
    # T=0.5: Still inside, duration < 1.0 -> No violation
    v = monitor.check_violations(dets, timestamp=t0 + 0.5)
    assert len(v) == 0
    
    # T=1.1: Duration > 1.0 -> Violation
    v = monitor.check_violations(dets, timestamp=t0 + 1.1)
    assert len(v) == 1
    assert v[0].zone_id == "test_zone"
    assert v[0].object_id == 1
    
    # T=1.2: Exit -> State cleared
    v = monitor.check_violations([], timestamp=t0 + 1.2)
    assert len(v) == 0
    assert 1 not in monitor.state or "test_zone" not in monitor.state[1]

def test_objects_outside_zone():
    monitor = ZoneMonitor()
    monitor.zones = {
        "test_zone": Polygon([(0,0), (10,0), (10,10), (0,10)])
    }
    
    # Point at (20, 20)
    dets = [{"track_id": 1, "label": "person", "bbox": (20, 20, 20, 20)}]
    t0 = 1000.0
    
    monitor.check_violations(dets, timestamp=t0)
    assert "test_zone" not in monitor.state.get(1, {})
