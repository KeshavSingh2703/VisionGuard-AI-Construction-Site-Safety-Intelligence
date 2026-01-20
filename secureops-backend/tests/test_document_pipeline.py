"""Tests for document processing pipeline."""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from src.stages.input.pdf_loader import PDFLoader
from src.stages.documents.chunker import DocumentChunker
from src.stages.documents.embedder import DocumentEmbedder
from src.stages.documents.vector_store import VectorStore
from src.core.types import DocumentChunk


class TestPDFLoader:
    """Test PDF loader."""
    
    @patch('src.stages.input.pdf_loader.pdfplumber')
    def test_load_pdf(self, mock_pdfplumber):
        """Test PDF loading."""
        # Mock pdfplumber
        mock_pdf = Mock()
        mock_pdf.pages = [Mock(extract_text=Mock(return_value="Sample text"))]
        mock_pdf.metadata = {}
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
        
        loader = PDFLoader({"use_pdfplumber": True})
        
        with patch('pathlib.Path.exists', return_value=True):
            result = loader.load_pdf("test.pdf")
            
            assert "text" in result
            assert "pages" in result


class TestDocumentChunker:
    """Test document chunker."""
    
    def test_chunk_document(self):
        """Test document chunking."""
        chunker = DocumentChunker({
            "chunk_size": 100,
            "chunk_overlap": 20
        })
        
        text = "This is a sample document. " * 50  # ~1500 chars
        chunks = chunker.chunk_document(text, "doc123")
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)
        assert all(chunk.document_id == "doc123" for chunk in chunks)


class TestDocumentEmbedder:
    """Test document embedder."""
    
    @patch('src.stages.documents.embedder.OpenAIEmbeddings')
    def test_embed_chunks(self, mock_embeddings):
        """Test chunk embedding."""
        # Mock embeddings
        mock_emb = Mock()
        mock_emb.embed_documents.return_value = [[0.1] * 1536, [0.2] * 1536]
        mock_embeddings.return_value = mock_emb
        
        embedder = DocumentEmbedder()
        
        chunks = [
            DocumentChunk(
                chunk_id="1",
                document_id="doc1",
                content="Test content",
                chunk_index=0
            )
        ]
        
        embeddings = embedder.embed_chunks(chunks)
        
        assert len(embeddings) == len(chunks)
        assert all(isinstance(emb, np.ndarray) for emb in embeddings)


class TestVectorStore:
    """Test vector store."""
    
    @patch('src.stages.documents.vector_store.get_db_session')
    def test_store_chunks(self, mock_db):
        """Test storing chunks."""
        mock_session = Mock()
        mock_db.return_value.__enter__.return_value = mock_session
        mock_db.return_value.__exit__.return_value = None
        
        vector_store = VectorStore()
        
        chunks = [
            DocumentChunk(
                chunk_id="1",
                document_id="doc1",
                content="Test",
                chunk_index=0
            )
        ]
        embeddings = [np.random.rand(1536).astype(np.float32)]
        
        result = vector_store.store_chunks(chunks, embeddings)
        
        assert len(result) == len(chunks)
        mock_session.add.assert_called()
        mock_session.commit.assert_called()

