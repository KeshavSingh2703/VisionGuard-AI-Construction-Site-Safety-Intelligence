"""PDF text cleaning utilities."""

import re
from typing import Optional


class PDFCleaner:
    """Clean extracted PDF text."""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean PDF text."""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might interfere
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', text)
        
        # Normalize line breaks
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()
    
    @staticmethod
    def remove_headers_footers(text: str) -> str:
        """Remove common headers and footers."""
        # This is a simple implementation
        # More sophisticated approaches would use layout analysis
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip lines that look like page numbers
            if re.match(r'^\s*\d+\s*$', line):
                continue
            # Skip very short lines that might be headers/footers
            if len(line.strip()) < 3:
                continue
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)

