import sys
import os
import unittest
import numpy as np
from datetime import datetime, timedelta
from typing import List

# Add project root to path
sys.path.append(os.getcwd())

from src.core.types import Detection, VideoFrame
from src.stages.vision.ppe_rules import PPERuleEngine

class TestPPERules(unittest.TestCase):
    
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

    def test_strict_persistence(self):
        """Test Case 1: Violation starts only after 10 frames (~0.33s)."""
        print("\n--- Test 1: Strict Persistence (10 Frames) ---")
        
        # Run 5 frames of Missing Helmet ("no_helmet")
        evts = self.run_sequence(0.15, 1, ["no_helmet", "vest"]) # 0.15s = ~4 frames
        self.assertEqual(len(evts), 0, "Should ignore short burst < 10 frames")
        
        # Run 20 frames more (Total 25 > 10)
        evts = self.run_sequence(0.7, 1, ["no_helmet", "vest"], start_offset=0.15)
        self.assertTrue(len(evts) > 0, "Should trigger after 10 frames")
        print("✔ Triggered after persistence threshold")
        
        # Check event details
        evt = evts[-1]
        self.assertEqual(evt["track_id"], 1)
        self.assertIn("helmet", evt["missing_items"])
        
    def test_recovery(self):
        """Test Case 2: Recovery requires 3 consecutive frames."""
        print("\n--- Test 2: Recovery Logic ---")
        
        # Create active violation (1s of missing)
        self.run_sequence(1.0, 2, ["no_helmet", "vest"])
        state = self.engine.track_states[2]["helmet"]
        self.assertTrue(state["active_violation"], "Should be active")
        
        # 1 frame of compliance
        self.run_sequence(0.033, 2, ["helmet", "vest"], start_offset=1.0)
        state = self.engine.track_states[2]["helmet"]
        self.assertTrue(state["active_violation"], "Should NOT clear after 1 frame")
        
        # 5 frames of compliance -> Should clear
        self.run_sequence(0.2, 2, ["helmet", "vest"], start_offset=1.033)
        state = self.engine.track_states[2]["helmet"]
        self.assertFalse(state["active_violation"], "Should clear after >3 frames")
        print("✔ Recovery verified")

    def test_unknown_persistence(self):
        """Test Case 3: Unknown frames do not reset counters."""
        print("\n--- Test 3: Unknown Persistence ---")
        
        # 8 frames Missing (Counter=8, Threshold=10)
        self.run_sequence(0.27, 3, ["no_helmet", "vest"]) 
        state = self.engine.track_states[3]["helmet"]
        self.assertEqual(state["missing_count"], 8)
        
        # 5 frames Unknown (No Helmet, No No_Helmet)
        # Passed as just ["vest"], so Helmet is implicit Unknown
        self.run_sequence(0.16, 3, ["vest"], start_offset=0.26)
        
        state = self.engine.track_states[3]["helmet"]
        self.assertEqual(state["missing_count"], 8, "Count should persist through Unknown")
        self.assertEqual(state["present_count"], 0, "Present count should remain 0")
        
        # 3 frames Missing -> Should trigger (8+3=11 > 10)
        evts = self.run_sequence(0.1, 3, ["no_helmet", "vest"], start_offset=0.42)
        state = self.engine.track_states[3]["helmet"]
        self.assertTrue(state["active_violation"], "Should trigger after accumulating frames")
        print("✔ Unknown frames handled correctly")

if __name__ == '__main__':
    unittest.main()
