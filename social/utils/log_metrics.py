"""
Log Metrics Module
-----------------
Provides functionality for tracking and aggregating logging metrics.
"""

from typing import Dict, Any
from datetime import datetime
from collections import defaultdict

class LogMetrics:
    """Tracks and aggregates logging metrics."""
    
    def __init__(self):
        """Initialize metrics tracking."""
        self.metrics = defaultdict(int)
        self.start_time = datetime.now()
        self.total_logs = 0
        self.errors = []
        self.rotations = 0
    
    def increment(self, metric_name: str, value: int = 1) -> None:
        """Increment a metric counter.
        
        Args:
            metric_name: Name of the metric to increment
            value: Amount to increment by (default: 1)
        """
        self.metrics[metric_name] += value
    
    def increment_logs(self, platform: str, level: str, status: str, format: str, size: int) -> None:
        """Increment log-related metrics.
        
        Args:
            platform: Platform name
            level: Log level
            status: Log status
            format: Log format
            size: Log size in bytes
        """
        self.total_logs += 1
        self.increment(f"{platform}.{level}.{status}")
        self.increment(f"{platform}.{format}")
        self.increment(f"{platform}.size", size)
    
    def record_error(self, error_message: str) -> None:
        """Record an error message.
        
        Args:
            error_message: Error message to record
        """
        self.errors.append({
            'message': error_message,
            'timestamp': datetime.now().isoformat()
        })
        self.increment('errors')
    
    def record_rotation(self) -> None:
        """Record a log rotation event."""
        self.rotations += 1
        self.increment('rotations')
    
    def get_metric(self, metric_name: str) -> int:
        """Get the current value of a metric.
        
        Args:
            metric_name: Name of the metric to get
            
        Returns:
            Current value of the metric
        """
        return self.metrics[metric_name]
    
    def get_all_metrics(self) -> Dict[str, int]:
        """Get all current metrics.
        
        Returns:
            Dictionary of all metrics and their values
        """
        return dict(self.metrics)
    
    def reset(self) -> None:
        """Reset all metrics to zero."""
        self.metrics.clear()
        self.start_time = datetime.now()
        self.total_logs = 0
        self.errors = []
        self.rotations = 0
    
    def get_uptime(self) -> float:
        """Get the uptime in seconds.
        
        Returns:
            Number of seconds since metrics started
        """
        return (datetime.now() - self.start_time).total_seconds() 