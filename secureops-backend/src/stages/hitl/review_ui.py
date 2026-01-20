"""Human review UI components."""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ReviewUI:
    """UI for human review."""
    
    def generate_review_interface(self, items: list) -> Dict[str, Any]:
        """Generate review interface data."""
        return {
            "items": items,
            "total": len(items)
        }

