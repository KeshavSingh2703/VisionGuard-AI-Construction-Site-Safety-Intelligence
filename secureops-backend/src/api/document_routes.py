"""Document processing routes."""

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from typing import Optional
import uuid
import os
import tempfile
from pathlib import Path
import logging

from src.pipeline.orchestrator import PipelineOrchestrator
from src.db.session import get_db_session
from src.db.models import Document, User
from src.api.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_id: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user)
):
    """Upload and process document."""
    if document_id is None:
        document_id = str(uuid.uuid4())
    
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Save uploaded file
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, f"{document_id}_{file.filename}")
    
    try:
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Process document in background
        orchestrator = PipelineOrchestrator()
        
        if background_tasks:
            background_tasks.add_task(orchestrator.process_document, temp_path, document_id)
        else:
            orchestrator.process_document(temp_path, document_id)
        
        return {
            "document_id": document_id,
            "status": "processing",
            "message": "Document uploaded and processing started"
        }
        
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}")
async def get_document(document_id: str, current_user: User = Depends(get_current_user)):
    """Get document information."""
    try:
        with get_db_session() as session:
            document = session.query(Document).filter(Document.document_id == document_id).first()
            
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")
            
            return {
                "document_id": document.document_id,
                "filename": document.filename,
                "status": document.status,
                "total_chunks": document.total_chunks,
                "created_at": document.created_at.isoformat() if document.created_at else None
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_documents(limit: int = 50, offset: int = 0, current_user: User = Depends(get_current_user)):
    """List all documents."""
    try:
        with get_db_session() as session:
            documents = session.query(Document).limit(limit).offset(offset).all()
            
            return {
                "documents": [
                    {
                        "document_id": d.document_id,
                        "filename": d.filename,
                        "status": d.status,
                        "total_chunks": d.total_chunks,
                        "created_at": d.created_at.isoformat() if d.created_at else None
                    }
                    for d in documents
                ],
                "count": len(documents)
            }
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}")
async def delete_document(document_id: str, current_user: User = Depends(get_current_user)):
    """Delete document and its vectors."""
    try:
        with get_db_session() as session:
            document = session.query(Document).filter(Document.document_id == document_id).first()
            
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")
            
            # Delete vectors
            from src.stages.documents.vector_store import VectorStore
            vector_store = VectorStore()
            vector_store.delete_document(document_id)
            
            # Delete document
            session.delete(document)
            session.commit()
            
            return {"message": f"Document {document_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

