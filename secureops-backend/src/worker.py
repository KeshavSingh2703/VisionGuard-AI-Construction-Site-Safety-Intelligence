import time
import sys
import logging
from src.db.session import get_db_session
from src.db.models import Upload
from src.pipeline.orchestrator import PipelineOrchestrator

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SecureOpsWorker")

def run_worker():
    """Poll DB for pending uploads and process them."""
    logger.info("👷 Worker Started. Waiting for jobs...")
    
    # Initialize Pipeline (Models loaded once)
    try:
        orchestrator = PipelineOrchestrator()
        logger.info("✅ Pipeline Orchestrator Initialized (Models Loaded)")
    except Exception as e:
        logger.error(f"❌ Failed to initialize pipeline: {e}")
        sys.exit(1)

    while True:
        try:
            processed = False
            with get_db_session() as session:
                # Find pending upload
                # Lock row if possible, but for simple local queue, fetch first pending
                job = session.query(Upload).filter(Upload.status == 'pending').first()
                
                if job:
                    upload_id = str(job.id)
                    file_path = job.stored_path
                    logger.info(f"🚀 Found Job: {upload_id} ({file_path})")
                    
                    # Process
                    # Note: Orchestrator handles status updates (processing -> completed)
                    # We pass the ID so it knows which record to update.
                    try:
                        orchestrator.process_video(file_path, video_id=upload_id)
                        logger.info(f"✅ Job Completed: {upload_id}")
                    except Exception as err:
                        logger.error(f"❌ Job Failed: {upload_id} - {err}")
                        # Orchestrator handles failed status update usually, 
                        # but check logic to be sure? 
                        # Orchestrator catches Exception and sets 'failed'.
                    
                    processed = True
            
            if not processed:
                time.sleep(2) # Sleep if no jobs
                
        except KeyboardInterrupt:
            logger.info("🛑 Worker Stopping...")
            break
        except Exception as e:
            logger.error(f"⚠️ Worker Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_worker()
