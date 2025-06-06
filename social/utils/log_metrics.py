"""
Log metrics module for recording and tracking metrics.
"""

from typing import Any, Dict, Optional
from datetime import datetime

class LogMetrics:
    """Class for recording and managing metrics."""
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {}
        self.last_updated: Optional[datetime] = None
    
    def record_metric(self, name: str, value: Any) -> None:
        """Record a metric with the given name and value."""
        self.metrics[name] = value
        self.last_updated = datetime.now()
    
    def get_metric(self, name: str) -> Optional[Any]:
        """Get the value of a metric by name."""
        return self.metrics.get(name)
    
    def clear_metrics(self) -> None:
        """Clear all recorded metrics."""
        self.metrics.clear()
        self.last_updated = None

# Create a singleton instance
metrics = LogMetrics()

def record_metric(name: str, value: Any) -> None:
    """Record a metric using the singleton instance."""
    metrics.record_metric(name, value)

def get_metric(name: str) -> Optional[Any]:
    """Get a metric value using the singleton instance."""
    return metrics.get_metric(name)

def clear_metrics() -> None:
    """Clear all metrics using the singleton instance."""
    metrics.clear_metrics() 