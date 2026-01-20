import shutil
import logging
import os
from pathlib import Path
from src.db.session import drop_db, init_db

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_filesystem():
    """Remove generated files."""
    paths_to_clean = [
        Path("data/uploads"),
        Path("data/reports"),
        Path("runs/detect"),
        Path("temp_shwd_dataset"),
        Path("data/safety_dataset")
    ]
    
    for p in paths_to_clean:
        if p.exists():
            logger.info(f"Cleaning {p}...")
            # If it's a directory, remove contents but keep dir if it's a standard one? 
            # actually better to just remove and recreate
            try:
                if p.is_dir():
                    shutil.rmtree(p)
                else:
                    p.unlink()
            except Exception as e:
                logger.warning(f"Failed to clean {p}: {e}")
                
    # Recreate essential dirs
    Path("data/uploads").mkdir(parents=True, exist_ok=True)
    Path("data/reports").mkdir(parents=True, exist_ok=True)
    logger.info("Filesystem cleaned.")

def reset_database():
    """Reset database tables."""
    logger.info("Dropping database tables...")
    drop_db()
    logger.info("Recreating database tables...")
    init_db()
    logger.info("Database reset complete.")

if __name__ == "__main__":
    confirm = input("This will DELETE ALL DATA (DB + Files). Type 'yes' to proceed: ")
    if confirm.lower() == 'yes':
        clean_filesystem()
        reset_database()
        logger.info("Cleanup successful!")
    else:
        logger.info("Cleanup cancelled.")
