"""
Log Metrics Module
----------------
Tracks metrics for logging operations.
"""

import time
from typing import Dict, Optional
from datetime import datetime

class LogMetrics:
    """Tracks metrics for logging operations."""
    
    def __init__(self):
        """Initialize metrics tracking."""
        self.start_time = time.time()
        self.total_logs = 0
        self.total_bytes = 0
        self.error_count = 0
        self.rotation_count = 0
        self.last_rotation = None
        self.format_counts = {}
        self.level_counts = {}
    
    def increment_logs(
        self,
        bytes_written: int = 0,
        format_type: Optional[str] = None,
        level: Optional[str] = None
    ) -> None:
        """Increment log count and format/level stats.
        
        Args:
            bytes_written: Number of bytes written
            format_type: Type of log format (e.g. 'json', 'text')
            level: Log level (e.g. 'INFO', 'ERROR')
        """
        self.total_logs += 1
        self.total_bytes += bytes_written
        
        if format_type:
            self.format_counts[format_type] = self.format_counts.get(format_type, 0) + 1
            
        if level:
            self.level_counts[level] = self.level_counts.get(level, 0) + 1
    
    def record_error(self) -> None:
        """Record a logging error."""
        self.error_count += 1
    
    def record_rotation(self) -> None:
        """Record a log rotation."""
        self.rotation_count += 1
        self.last_rotation = datetime.now()
    
    def get_metrics(self) -> Dict:
        """Get current metrics.
        
        Returns:
            Dict containing all metrics
        """
        return {
            'total_logs': self.total_logs,
            'total_bytes': self.total_bytes,
            'error_count': self.error_count,
            'rotation_count': self.rotation_count,
            'last_rotation': self.last_rotation,
            'format_counts': self.format_counts,
            'level_counts': self.level_counts,
            'uptime': self.get_uptime()
        }
    
    def reset(self) -> None:
        """Reset all metrics."""
        self.__init__()
    
    def get_uptime(self) -> float:
        """Get uptime in seconds.
        
        Returns:
            Uptime in seconds
        """
        return time.time() - self.start_time 
