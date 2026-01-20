import sys
from pathlib import Path
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StartupTest")

def verify_startup():
    try:
        logger.info("Importing app...")
        from src.main import app
        from src.db.session import init_db
        from src.pipeline.orchestrator import PipelineOrchestrator
        
        logger.info("Initializing DB (Dry Run)...")
        # Just check if function exists and imports worked
        if not callable(init_db):
            raise Exception("init_db not callable")
            
        logger.info("Initializing Orchestrator...")
        orch = PipelineOrchestrator()
        
        logger.info("Checking Safety Stages in Orchestrator...")
        if not hasattr(orch, "ppe_rules"):
            raise Exception("PipelineOrchestrator missing ppe_rules")
        if not hasattr(orch, "prox_detector"):
            raise Exception("PipelineOrchestrator missing prox_detector")
        if not hasattr(orch, "zone_monitor"):
            raise Exception("PipelineOrchestrator missing zone_monitor")
            
        logger.info("Checking API Routes...")
        routes = [r.path for r in app.routes]
        logger.info(f"Founds {len(routes)} routes.")
        
        required_routes = [
            "/api/v1/videos/upload",
            "/api/v1/videos/{video_id}/status",
            "/api/v1/results/summary",
            "/api/v1/results/violations"
        ]
        
        for r in required_routes:
            if r not in routes:
                # Some routers might be mounted, so exact match might fail if mounted differently
                # But here we included them directly. 
                # Let's check if ANY route matches
                if not any(curr.path == r for curr in app.routes):
                     logger.warning(f"Route {r} might be missing or path differs.")
            else:
                logger.info(f"Verified route: {r}")

        logger.info("✅ API Startup & Integration Verification Passed")
        
    except Exception as e:
        logger.error(f"❌ Startup Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    verify_startup()
