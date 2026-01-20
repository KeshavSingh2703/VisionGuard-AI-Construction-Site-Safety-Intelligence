"""Human-in-the-loop router."""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class HITLRouter:
    """Route items for human review."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.review_threshold = self.config.get("review_threshold", 0.5)
    
    def should_review(self, confidence: float) -> bool:
        """Determine if item should be reviewed."""
        return confidence < self.review_threshold

