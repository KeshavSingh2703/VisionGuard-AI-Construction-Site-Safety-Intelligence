"""Text embedding generation using LangChain."""

from typing import List, Optional, Dict, Any
import numpy as np
import logging

try:
    from langchain_huggingface import HuggingFaceEmbeddings
    LANGCHAIN_AVAILABLE = True
except ImportError:
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        LANGCHAIN_AVAILABLE = True
    except ImportError:
        LANGCHAIN_AVAILABLE = False

from src.core.base import BaseStage
from src.core.types import DocumentChunk
from src.core.exceptions import DocumentProcessingError
from src.core.config import get_config

logger = logging.getLogger(__name__)


class DocumentEmbedder(BaseStage):
    """Generate embeddings for document chunks."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.embedding_model = None
        self._initialize_embeddings()
    
    def _initialize_embeddings(self):
        """Initialize embedding model."""
        if not LANGCHAIN_AVAILABLE:
            logger.warning("LangChain/HuggingFace not available, embeddings will be mocked")
            return
        
        try:
            app_config = get_config()
            emb_config = app_config.embeddings
            
            if emb_config.provider == "huggingface":
                self.embedding_model = HuggingFaceEmbeddings(
                    model_name=emb_config.model,
                    encode_kwargs={'normalize_embeddings': getattr(emb_config, 'normalize', True)}
                )
                logger.info(f"Initialized HuggingFace embeddings: {emb_config.model}")
            else:
                logger.warning(f"Unsupported embedding provider: {emb_config.provider}, falling back to mocks")
                
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {e}")
            # Continue without embeddings for testing
            self.embedding_model = None
    
    def process(self, input_data: Any) -> Any:
        """Process document chunks."""
        if isinstance(input_data, list):
            return self.embed_chunks(input_data)
        elif isinstance(input_data, DocumentChunk):
            return self.embed_chunk(input_data)
        elif input_data is None:
             # Support mock/test calls
             return None
        else:
            raise ValueError(f"Unsupported input type: {type(input_data)}")
    
    def embed_chunks(self, chunks: List[DocumentChunk]) -> List[np.ndarray]:
        """Embed multiple chunks."""
        if not self.embedding_model:
            # Return mock embeddings for testing (384 dim)
            logger.warning("Using mock embeddings (384 dim)")
            return [np.random.rand(384).astype(np.float32) for _ in chunks]
        
        try:
            texts = [chunk.content for chunk in chunks]
            embeddings = self.embedding_model.embed_documents(texts)
            
            # Convert to numpy arrays
            return [np.array(emb, dtype=np.float32) for emb in embeddings]
            
        except Exception as e:
            logger.error(f"Failed to embed chunks: {e}")
            raise DocumentProcessingError(f"Embedding failed: {e}") from e
    
    def embed_chunk(self, chunk: DocumentChunk) -> np.ndarray:
        """Embed single chunk."""
        if not self.embedding_model:
            # Return mock embedding for testing
            logger.warning("Using mock embedding (384 dim)")
            return np.random.rand(384).astype(np.float32)
        
        try:
            embedding = self.embedding_model.embed_query(chunk.content)
            return np.array(embedding, dtype=np.float32)
            
        except Exception as e:
            logger.error(f"Failed to embed chunk: {e}")
            raise DocumentProcessingError(f"Embedding failed: {e}") from e

