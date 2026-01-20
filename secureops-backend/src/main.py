"""Main application entry point."""

import uvicorn
import logging
import os
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load .env file from project root
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        # Try loading from current directory
        load_dotenv()
except ImportError:
    # python-dotenv not installed, continue without it
    pass

from .api import create_app
from .db.session import init_db
from .core.config import get_config
from .core.logging import setup_logging
from .core.recovery import JobRecoveryManager
from .core.cleanup import CleanupManager

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


from fastapi.staticfiles import StaticFiles

# Create FastAPI app
app = create_app()

# Mount static files for media (violations images)
# Ensure storage directory exists
storage_path = Path("storage")
storage_path.mkdir(exist_ok=True)
app.mount("/media", StaticFiles(directory="storage"), name="media")

@app.on_event("startup")
async def startup_event():
    """Run startup tasks."""
    logger.info("Server starting up...")
    
    # 1. Job Recovery
    JobRecoveryManager.reset_stuck_jobs()
    
    # 2. Early Cleanup
    CleanupManager.purge_temp_files(max_age_hours=24)


def main():
    """Main application entry point."""
    # Load configuration
    config = get_config()
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # Continue anyway for development
    
    # Run server
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"Starting SecureOps API server on {host}:{port}")
    
    uvicorn.run(
        "src.main:app", # functional string import for real reloading
        host=host,
        port=port,
        log_level=config.logging.level.lower(),
        reload=True # Enable reload for dev convenience
    )


if __name__ == "__main__":
    main()

