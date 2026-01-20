"""Metrics collection."""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collect and track application metrics."""
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {
            "requests": 0,
            "errors": 0,
            "videos_processed": 0,
            "documents_processed": 0,
            "detections": 0,
            "start_time": datetime.now().isoformat()
        }
    
    def increment(self, metric: str, value: int = 1):
        """Increment metric."""
        if metric not in self.metrics:
            self.metrics[metric] = 0
        self.metrics[metric] += value
    
    def set(self, metric: str, value: Any):
        """Set metric value."""
        self.metrics[metric] = value
    
    def get(self, metric: Optional[str] = None) -> Any:
        """Get metric(s)."""
        if metric:
            return self.metrics.get(metric)
        return self.metrics.copy()
    
    def reset(self):
        """Reset all metrics."""
        self.metrics = {
            "requests": 0,
            "errors": 0,
            "videos_processed": 0,
            "documents_processed": 0,
            "detections": 0,
            "start_time": datetime.now().isoformat()
        }


# Global metrics collector
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector

