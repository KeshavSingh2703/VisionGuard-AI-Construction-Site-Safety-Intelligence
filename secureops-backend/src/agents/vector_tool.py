"""Vector search service."""

import logging
from src.stages.documents.vector_store import VectorStore

logger = logging.getLogger(__name__)

class VectorTool:
    """Vector search service (non-LangChain)."""
    
    def __init__(self, vector_store):
        self.vector_store = vector_store

    def search(self, embedding, top_k=5):
        """Search vector store using embedding."""
        return self.vector_store.search(embedding, top_k)
