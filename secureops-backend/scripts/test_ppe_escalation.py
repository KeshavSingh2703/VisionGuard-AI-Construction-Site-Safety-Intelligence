import sys
import os
import unittest
from datetime import datetime, timedelta
from typing import List
import numpy as np

# Add project root to path
sys.path.append(os.getcwd())

from src.core.types import Detection, VideoFrame
from src.stages.vision.ppe_rules import PPERuleEngine

class TestPPEEscalation(unittest.TestCase):
    
    def setUp(self):
        self.engine = PPERuleEngine()
        self.start_time = datetime.now()
        
    def run_sequence(self, duration_sec: float, track_id: int, classes: List[str], start_offset: float = 0.0):
        """Run a sequence of frames for duration_sec at 30FPS."""
        frames = int(duration_sec * 30)
        events = []
        
        for i in range(frames):
            time_offset = start_offset + (i / 30.0)
            ts = self.start_time + timedelta(seconds=time_offset)
            
            detections = []
            # Person
            detections.append(Detection(
                class_id=0, class_name="person", confidence=0.9, 
                bbox=[0,0,100,100], frame_number=int(time_offset*30), timestamp=ts,
                metadata={"track_id": track_id}
            ))
            
            # PPE
            for c in classes:
                detections.append(Detection(
                    class_id=1, class_name=c, confidence=0.9,
                    bbox=[0,0,50,50], frame_number=int(time_offset*30), timestamp=ts,
                    metadata={"track_id": track_id}
                ))
            
            frame = VideoFrame(
                frame_number=int(time_offset*30),
                timestamp=ts,
                image=np.zeros((100,100,3), dtype=np.uint8),
                detections=detections
            )
            
            new_events = self.engine.check_compliance(frame)
            events.extend(new_events)
            
        return events

    def test_unknown_escalation(self):
        """Test Case: Unknown status escalates to Missing after 5s."""
        print("\n--- Test: Unknown Escalation (>5s) ---")
        
        # 0. Initial Known State (Vest Present)
        self.run_sequence(1.0, 1, ["vest", "helmet"])
        
        # 1. Unknown for 4.0s (Just ["vest"] = Helmet Unknown)
        # Should persist (No Violation)
        evts = self.run_sequence(4.0, 1, ["vest"], start_offset=1.0)
        self.assertEqual(len(evts), 0, "Should persist unknown state < 5s")
        
        # Check internal state
        state = self.engine.track_states[1]["helmet"]
        self.assertIsNotNone(state.get("unknown_start"), "Timer should be running")
        self.assertEqual(state["missing_count"], 0, "Should not count as missing yet")
        
        # 2. Unknown for 1.5s more (Total 5.5s > 5.0s) -> ESCALATE
        # Note: Escalation increments missing_count. 
        # Trigger requires 10 frames of missing_count.
        # So we need enough frames AFTER escalation triggers to hit threshold.
        # 1.5s is plenty (~45 frames).
        
        evts = self.run_sequence(1.5, 1, ["vest"], start_offset=5.0)
        
        # Expectation: After 5.0s total unknown time, missing_count starts incrementing.
        # It needs 10 frames (~0.33s) to trigger active_violation.
        
        self.assertTrue(len(evts) > 0, "Should trigger violation after timeout + threshold")
        
        evt = evts[-1]
        self.assertIn("helmet", evt["missing_items"])
        self.assertEqual(evt["track_id"], 1)
        print("✔ Escalation verified")
        
    def test_unknown_reset(self):
        """Test Case: Timer resets if status becomes known."""
        print("\n--- Test: Unknown Timer Reset ---")
        
        # 1. Unknown for 3.0s (Helmet Unknown)
        self.run_sequence(3.0, 2, ["vest"])
        state = self.engine.track_states[2]["helmet"]
        self.assertIsNotNone(state.get("unknown_start"))
        
        # 2. Known (Helmet Present) for 1 frame
        self.run_sequence(0.1, 2, ["vest", "helmet"], start_offset=3.0)
        state = self.engine.track_states[2]["helmet"]
        self.assertIsNone(state.get("unknown_start"), "Timer should reset")
        
        # 3. Unknown again for 3.0s
        self.run_sequence(3.0, 2, ["vest"], start_offset=3.1)
        state = self.engine.track_states[2]["helmet"]
        self.assertIsNotNone(state.get("unknown_start"))
        self.assertEqual(state["missing_count"], 0, "Should count from 0 again")
        print("✔ Reset logic verified")

if __name__ == '__main__':
    unittest.main()
