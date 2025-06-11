"""
Log Metrics Module
----------------
Specialized metrics for logging operations.
"""

from typing import Dict, Optional
from datetime import datetime
from .base import BaseMetrics

class LogMetrics(BaseMetrics):
    """Metrics for logging operations."""
    
    def __init__(self, metrics_dir: Optional[str] = None):
        """Initialize log metrics.
        
        Args:
            metrics_dir: Optional directory to store metrics
        """
        super().__init__("log_metrics", metrics_dir)
        self.last_error: Optional[datetime] = None
        self.last_error_message: Optional[str] = None
        self.last_rotation: Optional[datetime] = None
        
    def record_log(self, level: str, platform: str, status: str = "success") -> None:
        """Record a log entry.
        
        Args:
            level: Log level (e.g. 'INFO', 'ERROR')
            platform: Platform name
            status: Status of the log operation
        """
        self.increment("log_entries", tags={
            "level": level.lower(),
            "platform": platform,
            "status": status
        })
        
    def record_error(self, message: str) -> None:
        """Record a logging error.
        
        Args:
            message: Error message
        """
        self.increment("log_errors")
        self.last_error = datetime.now()
        self.last_error_message = message
        
    def record_rotation(self) -> None:
        """Record a log rotation."""
        self.increment("log_rotations")
        self.last_rotation = datetime.now()
        
    def get_metrics(self) -> Dict:
        """Get current metrics.
        
        Returns:
            Dictionary containing all metrics
        """
        metrics = super().get_metrics()
        metrics.update({
            "last_error": self.last_error.isoformat() if self.last_error else None,
            "last_error_message": self.last_error_message,
            "last_rotation": self.last_rotation.isoformat() if self.last_rotation else None
        })
        return metrics 