"""Vector store using PostgreSQL pgvector."""

from typing import List, Optional, Dict, Any
import numpy as np
from sqlalchemy import text
import json
import logging

from src.core.base import BaseStage
from src.core.types import DocumentChunk, VectorSearchResult
from src.core.exceptions import DatabaseError
from src.db.session import get_db_session
from src.db.models import DocumentVector
from src.core.config import get_config

logger = logging.getLogger(__name__)


class VectorStore(BaseStage):
    """Vector store for document embeddings."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        app_config = get_config()
        self.table_name = app_config.vector_store.table_name
        self.similarity_threshold = app_config.vector_store.similarity_threshold
        self.top_k = app_config.vector_store.top_k
    
    def process(self, input_data: Any) -> Any:
        """Process vector operations."""
        if isinstance(input_data, dict):
            operation = input_data.get("operation")
            if operation == "store":
                return self.store_chunks(
                    input_data["chunks"],
                    input_data["embeddings"]
                )
            elif operation == "search":
                return self.search(
                    input_data["query_embedding"],
                    input_data.get("document_id")
                )
            else:
                raise ValueError(f"Unknown operation: {operation}")
        else:
            raise ValueError(f"Unsupported input type: {type(input_data)}")
    
    def store_chunks(
        self,
        chunks: List[DocumentChunk],
        embeddings: List[np.ndarray]
    ) -> List[str]:
        """Store document chunks with embeddings."""
        if len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings must have same length")
        
        stored_ids = []
        
        try:
            with get_db_session() as session:
                for chunk, embedding in zip(chunks, embeddings):
                    # Convert numpy array to list for pgvector
                    embedding_list = embedding.tolist()
                    
                    vector_record = DocumentVector(
                        document_id=chunk.document_id,
                        embedding=embedding_list,  # pgvector will handle conversion
                        content=chunk.content, # Correct column from model
                        metadata_=chunk.metadata # Correct column attribute from model
                    )
                    
                    session.add(vector_record)
                    stored_ids.append(chunk.chunk_id)
                
                session.commit()
                logger.info(f"Stored {len(stored_ids)} chunks in vector store")
                
        except Exception as e:
            logger.error(f"Failed to store chunks: {e}")
            raise DatabaseError(f"Vector store failed: {e}") from e
        
        return stored_ids
    
    def search(
        self,
        query_embedding: np.ndarray,
        document_id: Optional[str] = None
    ) -> List[VectorSearchResult]:
        """Search similar chunks."""
        try:
            query_vector = query_embedding.tolist()
            
            with get_db_session() as session:
                # Use raw SQL for pgvector cosine distance
                # pgvector uses <=> operator for cosine distance
                vector_str = "[" + ",".join(map(str, query_vector)) + "]"
                
                sql = text("""
                    SELECT id, document_id, content, metadata,
                           1 - (embedding <=> :query_vector::vector) as similarity
                    FROM document_vectors
                    WHERE 1 - (embedding <=> :query_vector::vector) >= :threshold
                    {document_filter}
                    ORDER BY embedding <=> :query_vector::vector
                    LIMIT :limit
                """.format(
                    document_filter="AND document_id = :document_id" if document_id else ""
                ))
                
                params = {
                    "query_vector": vector_str,
                    "threshold": self.similarity_threshold,
                    "limit": self.top_k
                }
                
                if document_id:
                    params["document_id"] = document_id
                
                results = session.execute(sql, params).fetchall()
                
                # Convert to VectorSearchResult
                search_results = []
                for row in results:
                    # Parse metadata if it's a string
                    metadata = getattr(row, "extra_metadata", None)
                    if isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                        except:
                            metadata = {}
                    elif metadata is None:
                        metadata = {}
                    
                    search_result = VectorSearchResult(
                        chunk_id=str(row.id), # Use DB ID as chunk ID since we don't store chunk_id explicitly anymore
                        document_id=str(row.document_id),
                        content=row.content,
                        similarity=float(row.similarity),
                        metadata=metadata
                    )
                    search_results.append(search_result)
                
                logger.info(f"Found {len(search_results)} similar chunks")
                return search_results
                
        except Exception as e:
            logger.error(f"Failed to search vector store: {e}")
            raise DatabaseError(f"Vector search failed: {e}") from e
    
    def delete_document(self, document_id: str) -> int:
        """Delete all chunks for a document."""
        try:
            with get_db_session() as session:
                deleted = session.query(DocumentVector).filter(
                    DocumentVector.document_id == document_id
                ).delete()
                
                session.commit()
                logger.info(f"Deleted {deleted} chunks for document {document_id}")
                return deleted
                
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            raise DatabaseError(f"Delete failed: {e}") from e

