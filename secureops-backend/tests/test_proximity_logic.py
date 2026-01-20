import time
import pytest
from src.stages.vision.proximity import ProximityDetector

def make_person(pid, bbox):
    return {"track_id": pid, "bbox": bbox}

def make_machine(label, bbox):
    return {"label": label, "bbox": bbox}

def test_warning_trigger_after_time():
    detector = ProximityDetector()
    
    # Setup: 1000x1000 image, Diagonal ~1414px
    # Warning Threshold 0.15 * 1414 = 212px
    # Critical Threshold 0.08 * 1414 = 113px
    
    # Person at (150, 150) center
    person = make_person(1, (100, 100, 200, 200))
    # Machine at (300, 150) center -> Dist = 150px
    # 150 < 212 (Warning) but > 113 (Critical)
    machine = make_machine("excavator", (250, 100, 350, 200))

    w, h = 1000, 1000
    t0 = time.time()

    # Initial frame — no event (buffer)
    events = detector.process([person], [machine], w, h, now=t0)
    assert events == []

    # After 0.6s (>= 0.5s) → WARNING should fire
    events = detector.process([person], [machine], w, h, now=t0 + 0.6)
    assert len(events) == 1
    assert events[0].severity == "WARNING"

def test_critical_trigger_after_time():
    detector = ProximityDetector()
    
    # 1000x1000 image
    # Critical threshold ~113px
    
    # Person at (150, 150) center
    person = make_person(1, (100, 100, 200, 200))
    # Machine at (200, 150) center -> Dist = 50px
    # 50 < 113 (Critical)
    machine = make_machine("dump_truck", (150, 100, 250, 200))

    w, h = 1000, 1000
    t0 = time.time()

    # Below critical threshold, initially nothing
    events = detector.process([person], [machine], w, h, now=t0)
    assert events == []

    # After 1.1s (>= 1.0s) -> CRITICAL
    events = detector.process([person], [machine], w, h, now=t0 + 1.1)
    assert len(events) == 1
    assert events[0].severity == "CRITICAL"

def test_glitch_does_not_trigger():
    detector = ProximityDetector()

    persons = [make_person(1, (100, 100, 200, 200))]
    machines = [make_machine("excavator", (250, 100, 350, 200))]

    w, h = 1000, 1000
    t0 = time.time()

    detector.process(persons, machines, w, h, now=t0)
    detector.process(persons, machines, w, h, now=t0 + 0.3)

    # glitch duration 0.3s < WARNING_TIME (0.5s)
    # Next frame empty -> cleanup
    events = detector.process([], [], w, h, now=t0 + 0.4)
    assert events == []
    
    # Even if person reappears, timer should restart (impl specific)
