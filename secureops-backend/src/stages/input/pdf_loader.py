"""PDF loader for document processing."""

import cv2
import numpy as np
from typing import List, Optional, Dict, Any
from pathlib import Path
import logging

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

from src.core.base import BaseStage
from src.core.exceptions import DocumentProcessingError

logger = logging.getLogger(__name__)


class PDFLoader(BaseStage):
    """Load and extract text from PDF files."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.use_pdfplumber = self.config.get("use_pdfplumber", True)
    
    def process(self, input_data: Any) -> Any:
        """Process PDF file."""
        if isinstance(input_data, str):
            return self.load_pdf(input_data)
        elif isinstance(input_data, Path):
            return self.load_pdf(str(input_data))
        else:
            raise ValueError(f"Unsupported input type: {type(input_data)}")
    
    def load_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Load PDF and extract text."""
        if not Path(pdf_path).exists():
            raise DocumentProcessingError(f"PDF file not found: {pdf_path}")
        
        try:
            if self.use_pdfplumber and PDFPLUMBER_AVAILABLE:
                return self._load_with_pdfplumber(pdf_path)
            elif PDF_AVAILABLE:
                return self._load_with_pypdf2(pdf_path)
            else:
                raise DocumentProcessingError(
                    "No PDF library available. Install pdfplumber or PyPDF2"
                )
        except Exception as e:
            logger.error(f"Failed to load PDF {pdf_path}: {e}")
            raise DocumentProcessingError(f"PDF loading failed: {e}") from e
    
    def load_pdf_images(self, pdf_path: str) -> List[np.ndarray]:
        """Load PDF pages as images (numpy arrays) for vision processing."""
        if not Path(pdf_path).exists():
            raise DocumentProcessingError(f"PDF file not found: {pdf_path}")
            
        if not PDFPLUMBER_AVAILABLE:
             raise DocumentProcessingError("pdfplumber required for image extraction")
             
        try:
            import pdfplumber
            images = []
            with pdfplumber.open(pdf_path) as pdf:
                logger.info(f"Converting PDF to images: {pdf_path} ({len(pdf.pages)} pages)")
                for page in pdf.pages:
                    # Convert to image (200 DPI is good balance)
                    im = page.to_image(resolution=200).original
                    # Convert PIL to numpy (RGB)
                    open_cv_image = np.array(im) 
                    # Convert RGB to BGR 
                    open_cv_image = open_cv_image[:, :, ::-1].copy() 
                    images.append(open_cv_image)
            
            return images
        except Exception as e:
            logger.error(f"Failed to extract images from PDF {pdf_path}: {e}")
            raise DocumentProcessingError(f"PDF image extraction failed: {e}") from e

    def _load_with_pdfplumber(self, pdf_path: str) -> Dict[str, Any]:
        """Load PDF using pdfplumber."""
        import pdfplumber
        
        text_pages = []
        metadata = {}
        
        with pdfplumber.open(pdf_path) as pdf:
            metadata = {
                "total_pages": len(pdf.pages),
                "metadata": pdf.metadata or {}
            }
            
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    text_pages.append({
                        "page_number": page_num + 1,
                        "text": text
                    })
        
        return {
            "text": "\n\n".join([p["text"] for p in text_pages]),
            "pages": text_pages,
            "metadata": metadata
        }
    
    def _load_with_pypdf2(self, pdf_path: str) -> Dict[str, Any]:
        """Load PDF using PyPDF2."""
        import PyPDF2
        
        text_pages = []
        metadata = {}
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            metadata = {
                "total_pages": len(pdf_reader.pages),
                "metadata": pdf_reader.metadata or {}
            }
            
            for page_num, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                if text:
                    text_pages.append({
                        "page_number": page_num + 1,
                        "text": text
                    })
        
        return {
            "text": "\n\n".join([p["text"] for p in text_pages]),
            "pages": text_pages,
            "metadata": metadata
        }

