"""Text chunking for document processing."""

from typing import List, Dict, Any, Optional
import uuid
from src.core.base import BaseStage
from src.core.types import DocumentChunk
from src.core.exceptions import DocumentProcessingError
import logging

logger = logging.getLogger(__name__)


class DocumentChunker(BaseStage):
    """Chunk documents for vector storage."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.chunk_size = self.config.get("chunk_size", 1000)
        self.chunk_overlap = self.config.get("chunk_overlap", 200)
    
    def process(self, input_data: Any) -> Any:
        """Process document text."""
        if isinstance(input_data, dict):
            return self.chunk_document(
                input_data.get("text", ""),
                input_data.get("document_id", str(uuid.uuid4()))
            )
        elif isinstance(input_data, str):
            return self.chunk_document(input_data, str(uuid.uuid4()))
        else:
            raise ValueError(f"Unsupported input type: {type(input_data)}")
    
    def chunk_document(self, text: str, document_id: str) -> List[DocumentChunk]:
        """Chunk document text."""
        if not text:
            raise DocumentProcessingError("Empty text provided")
        
        try:
            chunks = []
            start = 0
            chunk_index = 0
            
            while start < len(text):
                # Calculate end position
                end = start + self.chunk_size
                
                # Extract chunk
                chunk_text = text[start:end]
                
                # Try to break at sentence boundary
                if end < len(text):
                    # Look for sentence endings
                    last_period = chunk_text.rfind('.')
                    last_newline = chunk_text.rfind('\n')
                    
                    break_point = max(last_period, last_newline)
                    if break_point > self.chunk_size * 0.5:  # Don't break too early
                        chunk_text = chunk_text[:break_point + 1]
                        end = start + break_point + 1
                
                # Create chunk
                chunk = DocumentChunk(
                    chunk_id=str(uuid.uuid4()),
                    document_id=document_id,
                    content=chunk_text.strip(),
                    chunk_index=chunk_index,
                    metadata={
                        "start": start,
                        "end": end,
                        "length": len(chunk_text)
                    }
                )
                
                chunks.append(chunk)
                chunk_index += 1
                
                # Move start position with overlap
                start = end - self.chunk_overlap
                if start >= len(text):
                    break
            
            logger.info(f"Created {len(chunks)} chunks for document {document_id}")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to chunk document: {e}")
            raise DocumentProcessingError(f"Chunking failed: {e}") from e

