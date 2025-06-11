"""Log metrics module for tracking logging statistics."""

from typing import Dict, Any
from datetime import datetime

__all__ = ['LogMetrics']

class LogMetrics:
    """Tracks metrics for logging operations."""
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {
            'total_logs': 0,
            'last_log_time': None,
            'errors': 0,
            'warnings': 0
        }
    
    def increment_logs(self):
        """Increment total log count."""
        self.metrics['total_logs'] += 1
        self.metrics['last_log_time'] = datetime.now()
    
    def increment_errors(self):
        """Increment error count."""
        self.metrics['errors'] += 1
    
    def increment_warnings(self):
        """Increment warning count."""
        self.metrics['warnings'] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return self.metrics.copy() 