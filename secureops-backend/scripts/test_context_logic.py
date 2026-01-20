import sys
import os
import unittest
from typing import List, Dict, Any

# Add project root
sys.path.append(os.getcwd())

from src.stages.aggregation.unified_stream import ViolationAggregator, UnifiedViolation

# Mock Repositories
class MockRepo:
    def __init__(self, data: List[Dict[str, Any]]):
        self.data = data
        
    def get_by_upload_id(self, upload_id: str):
        return self.data
        
    def get_events(self, upload_id: str):
        return self.data

class TestContextLogic(unittest.TestCase):
    
    def setUp(self):
        pass

    def test_safe_zone_suppression(self):
        """Test Case 1: Worker in Safe Zone + No Vest -> IGNORED (Safe)"""
        print("\n--- Test 1: Safe Zone Suppression ---")
        
        # 1. PPE Event: No Vest (Track 1)
        ppe_events = [{
            "timestamp": 100.0,
            "track_id": 1,
            "severity": "low",
            "extra_metadata": {"missing_items": ["vest"]} # Only vest missing
        }]
        
        # 2. No Risk Events (Safe Zone)
        prox_events = []
        zone_events = []
        
        aggregator = ViolationAggregator(
            MockRepo(ppe_events),
            MockRepo(prox_events),
            MockRepo(zone_events)
        )
        
        stream = aggregator.get_unified_stream("test_upload")
        
        # Assertions
        # Expecting 1 event, but severity should be SAFE (or filtered out if we ignored it? Logic says keeps it but marks SAFE)
        self.assertEqual(len(stream), 1)
        evt = stream[0]
        self.assertEqual(evt.severity, "safe", "Isolated vest violation in safe zone should be SAFE")
        self.assertTrue(evt.details.get("ignored"), "Should be marked as ignored")
        print("✔ Suppression verified")

    def test_risk_zone_escalation(self):
        """Test Case 2: Worker in Danger Zone + No Vest -> WARNING (Escalated)"""
        print("\n--- Test 2: Risk Zone Escalation ---")
        
        # 1. PPE Event: No Vest (Track 2)
        ppe_events = [{
            "timestamp": 100.0,
            "track_id": 2,
            "severity": "low",
            "extra_metadata": {"missing_items": ["vest"]}
        }]
        
        # 2. Zone Event: Risk Zone (Track 2)
        # UnifiedStream groups by integer timestamp, so match timestamp 100.0
        zone_events = [{
            "timestamp": 100.2, # Within 1s window
            "object_id": 2,
            "zone_id": "danger_zone_1"
        }]
        prox_events = []
        
        aggregator = ViolationAggregator(
            MockRepo(ppe_events),
            MockRepo(prox_events),
            MockRepo(zone_events)
        )
        
        stream = aggregator.get_unified_stream("test_upload")
        
        # We expect 2 events (PPE + Zone) in the stream, but PPE event should be escalated.
        ppe_evt = next((e for e in stream if e.violation_type == 'ppe'), None)
        
        self.assertIsNotNone(ppe_evt)
        self.assertEqual(ppe_evt.severity, "warning", "Vest + Risk Zone should escalate to WARNING")
        self.assertTrue(ppe_evt.details.get("escalated"), "Should be marked as escalated")
        print("✔ Escalation verified")

    def test_helmet_criticality(self):
        """Test Case 3: Worker + No Helmet -> CRITICAL (Always Alert)"""
        print("\n--- Test 3: Helmet Criticality ---")
        
        # 1. PPE Event: No Helmet (Track 3)
        ppe_events = [{
            "timestamp": 100.0,
            "track_id": 3,
            "severity": "medium",
            "extra_metadata": {"missing_items": ["helmet"]}
        }]
        
        # 2. Safe Zone (No other events)
        aggregator = ViolationAggregator(
            MockRepo(ppe_events),
            MockRepo([]),
            MockRepo([])
        )
        
        stream = aggregator.get_unified_stream("test_upload")
        
        self.assertEqual(len(stream), 1)
        evt = stream[0]
        
        # Helmet is always at least underlying severity (Medium/High).
        # Logic says: Case C (Ignore) only applies if 'helmet' NOT in missing.
        # So it should NOT be safe.
        self.assertNotEqual(evt.severity, "safe", "Helmet violation should NEVER be ignored")
        print("✔ Helmet priority verified")
        
    def test_helmet_risk_critical(self):
        """Test Case 4: Helmet + Risk -> CRITICAL"""
        print("\n--- Test 4: Helmet + Risk Criticality ---")
        
        ppe_events = [{
            "timestamp": 100.0,
            "track_id": 4,
            "severity": "medium",
            "extra_metadata": {"missing_items": ["helmet"]}
        }]
        
        prox_events = [{
            "timestamp": 100.1,
            "person_id": 4,
            "machine_type": "excavator", 
            "severity": "warning"
        }]
        
        aggregator = ViolationAggregator(
            MockRepo(ppe_events),
            MockRepo(prox_events),
            MockRepo([])
        )
        
        stream = aggregator.get_unified_stream("test_upload")
        ppe_evt = next((e for e in stream if e.violation_type == 'ppe'), None)
        
        self.assertEqual(ppe_evt.severity, "critical", "Helmet + Proximity should be CRITICAL")
        print("✔ Critical escalation verified")

if __name__ == '__main__':
    unittest.main()
