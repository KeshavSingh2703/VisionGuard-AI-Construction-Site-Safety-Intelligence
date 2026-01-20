from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends
from uuid import uuid4
import shutil
import aiofiles
from pathlib import Path
from src.db.session import get_session_local
from src.db.models import Upload, User
from src.api.deps import get_current_user
from src.pipeline.orchestrator import PipelineOrchestrator
import logging

from src.core.exceptions import ModelLoadError

# Configure logger
logger = logging.getLogger(__name__)

# Create Session factory
SessionLocal = get_session_local()

# Initialize Orchestrator (Loads ML models - done once on startup)
try:
    orchestrator = PipelineOrchestrator()
    logger.info("Pipeline Orchestrator Initialized")
except Exception as e:
    logger.error(f"Failed to initialize orchestrator: {e}")
    # We continue, but uploads might fail to process
    orchestrator = None

router = APIRouter(prefix="/api/v1/videos", tags=["uploads"])

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def run_pipeline(upload_id: str, path: str):
    """
    Background task to run the ML pipeline.
    CRITICAL: This must be a sync function (def, not async def) so FastAPI 
    runs it in a separate threadpool. ML operations are CPU-bound and blocking.
    """
    if not orchestrator:
        logger.error("Orchestrator not initialized. Skipping processing.")
        return
    
    logger.info(f"Starting background processing for {upload_id}")
    try:
        orchestrator.process_video(path, video_id=upload_id)
        logger.info(f"Finished processing {upload_id}")
    except ModelLoadError as mle:
        logger.critical(f"ML Model Loading Failed for {upload_id}: {mle}")
        # Could implicitly set status='failed' via orchestrator logic if it reached it, 
        # but orchestrator might have failed early.
        # We rely on orchestrator state handling for DB updates usually.
    except Exception as e:
        logger.error(f"Background processing failed for {upload_id}: {e}")

@router.post("/upload")
async def upload(
    background_tasks: BackgroundTasks, 
    upload_type: str = Form(...),
    files: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a single file for processing.
    Async handler to prevent blocking the event loop during file I/O.
    Constraints:
    - Image: <= 10MB (jpg, jpeg, png, bmp)
    - PDF: <= 50MB
    - Video: <= 100MB (mp4, mov, avi, mkv)
    """
    if orchestrator is None:
        raise HTTPException(
            status_code=503, 
            detail="ML Service Unavailable: Backend failed to initialize AI models."
        )

    if not files or len(files) != 1:
        raise HTTPException(status_code=400, detail="Please upload exactly one file.")

    if upload_type not in ["image", "pdf", "video"]:
        raise HTTPException(status_code=400, detail="Invalid upload_type. Must be 'image', 'pdf', or 'video'.")

    f = files[0]
    filename = f.filename.lower()
    
    # Determine type and limits
    LIMITS = {
        "image": 10 * 1024 * 1024,
        "pdf": 50 * 1024 * 1024,
        "video": 100 * 1024 * 1024
    }
    
    # Strict Type Validation
    valid_extensions = {
        "image": ('.jpg', '.jpeg', '.png', '.bmp'),
        "pdf": ('.pdf',),
        "video": ('.mp4', '.mov', '.avi', '.mkv')
    }
    
    if not filename.endswith(valid_extensions[upload_type]):
         allowed = ", ".join(valid_extensions[upload_type]).replace('.', '')
         raise HTTPException(
             status_code=400, 
             detail=f"Invalid file extension for {upload_type}. Allowed: {allowed}"
         )
    
    # Check size - Streaming check would be better but simple tell works for UploadFile SpooledFile
    # UploadFile behaves like a file-like object.
    # Note: For strict async, getting size via seek/tell might block if it's on disk? 
    # Usually UploadFile is in memory or spooled. This is acceptable for now.
    # Check size
    # UploadFile.file is the underlying SpooledTemporaryFile.
    # We access it synchronously because seek/tell are fast standard I/O ops.
    f.file.seek(0, 2)
    size = f.file.tell()
    f.file.seek(0)
    
    if size > LIMITS[upload_type]:
        limit_mb = LIMITS[upload_type] // (1024 * 1024)
        raise HTTPException(
            status_code=400, 
            detail=f"File too large. {upload_type.capitalize()} limit is {limit_mb}MB"
        )

    upload_id = uuid4()
    db = SessionLocal()
    try:
        safe_name = f"{upload_id}_{f.filename}"
        path = UPLOAD_DIR / safe_name

        # Async write to avoid blocking event loop
        async with aiofiles.open(path, "wb") as out_file:
            while content := await f.read(1024 * 1024):  # 1MB chunks
                await out_file.write(content)

        db.add(Upload(
            id=upload_id,
            upload_type=upload_type,
            original_filename=f.filename,
            stored_path=str(path),
            status="pending"
        ))

        db.commit()
        
        # Trigger background processing
        # run_pipeline is sync, so it runs in threadpool
        background_tasks.add_task(run_pipeline, str(upload_id), str(path))
        
        return {"video_id": str(upload_id), "status": "pending"}

    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.get("/{video_id}/status")
def status(video_id: str, current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        upload = db.query(Upload).filter(Upload.id == video_id).first()
        if not upload:
            return {"status": "failed"}
        return {
            "video_id": video_id,
            "status": upload.status
        }
    finally:
        db.close()
