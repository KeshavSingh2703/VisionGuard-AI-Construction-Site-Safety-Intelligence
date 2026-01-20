"""Job recovery management."""

import logging
from sqlalchemy.orm import Session
from src.db.session import get_db_session
from src.db.models import Upload, Document

logger = logging.getLogger(__name__)


class JobRecoveryManager:
    """Manage job recovery for interrupted tasks."""
    
    @staticmethod
    def reset_stuck_jobs():
        """Reset jobs stuck in processing state due to system restart."""
        try:
            with get_db_session() as session:
                # 1. Reset Uploads (Videos)
                stuck_uploads = session.query(Upload).filter(
                    Upload.status.in_(["processing", "uploading"])
                ).all()
                
                for upload in stuck_uploads:
                    logger.warning(f"Resetting stuck upload: {upload.id}")
                    upload.status = "failed"
                    # Add error reason in metadata if possible, but schema might not show it easily 
                    # without extra_metadata column on Upload. 
                    # Assuming we can just log it or if Upload has a message field.
                    # Looking at models.py, Upload has no message field.
                    # We will log it.
                
                # 2. Reset Documents (PDFs)
                stuck_docs = session.query(Document).filter(
                    Document.status == "processing"
                ).all()
                
                for doc in stuck_docs:
                    logger.warning(f"Resetting stuck document: {doc.document_id}")
                    doc.status = "failed"
                
                if stuck_uploads or stuck_docs:
                    session.commit()
                    logger.info(f"Recovery: Reset {len(stuck_uploads)} uploads and {len(stuck_docs)} documents to failed state.")
                else:
                    logger.info("Recovery: No stuck jobs found.")
                    
        except Exception as e:
            logger.error(f"Job recovery failed: {e}")
