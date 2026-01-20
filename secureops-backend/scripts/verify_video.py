import sys
import os
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO) # Keep root info to reduce noise
logging.getLogger("src").setLevel(logging.DEBUG) # Force src to valid debug
logger = logging.getLogger(__name__)

# Add src to path
sys.path.append(os.getcwd())

from src.pipeline.orchestrator import PipelineOrchestrator

def main():
    video_path = "data/videos/88231-602915804_small.mp4"
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        
    abs_path = os.path.abspath(video_path)
    
    if not os.path.exists(abs_path):
        logger.error(f"File not found: {abs_path}")
        return

    logger.info(f"Starting processing verification for: {abs_path}")
    
    try:
        orchestrator = PipelineOrchestrator()
        
        # Monkey patch PPERuleEngine.check_compliance to add debug logging
        original_check = orchestrator.ppe_rules.check_compliance
        
        def logging_check_compliance(frame, quality_score=1.0):
            # Run original logic
            events = original_check(frame, quality_score)
            
            # Additional Debug Logging
            import time
            current_time = frame.timestamp.timestamp()
            
            # Log state for active tracks
            states = orchestrator.ppe_rules.track_states
            for tid, state in states.items():
                if current_time - state["last_update"] > 1.0: continue # Skip stale tracks in log

                # Helmet status
                h_state = "PRESENT"
                if state["helmet"]["active_violation"]:
                    h_state = "MISSING"
                elif state["helmet"]["unknown_start"]:
                    dur = current_time - state["helmet"]["unknown_start"]
                    h_state = f"UNKNOWN ({dur:.1f}s)"
                
                # Vest status
                v_state = "PRESENT"
                if state["vest"]["active_violation"]:
                    v_state = "MISSING"
                elif state["vest"]["unknown_start"]:
                    dur = current_time - state["vest"]["unknown_start"]
                    v_state = f"UNKNOWN ({dur:.1f}s)"
                
                logger.info(f"Frame {frame.frame_number} | Track {tid} | Helmet: {h_state} | Vest: {v_state}")
                
            return events
            
        # Bind the method
        orchestrator.ppe_rules.check_compliance = logging_check_compliance

        # FORCE FULL VIDEO PROCESSING (1 FPS Interval -> 30 FPS Processing)
        # Default is often 30 (1 FPS) which breaks 5s logic check.
        orchestrator.video_loader.frame_interval = 1
        orchestrator.video_loader.max_frames = 3000
        logger.info("🔧 Configured for FULL VIDEO verification (Interval=1, MaxFrames=3000)")
        
        vid_id = orchestrator.process_video(abs_path)
        logger.info(f"✅ Processing Complete. Video ID: {vid_id}")
        
    except Exception as e:
        logger.error(f"❌ Processing Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
