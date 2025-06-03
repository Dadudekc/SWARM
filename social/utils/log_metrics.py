"""
Log Metrics Module
-----------------
Tracks and reports logging metrics.
"""

import logging
from typing import Dict, Any
from collections import defaultdict
import threading
import time
from datetime import datetime

logger = logging.getLogger("LogMetrics")

class LogMetrics:
    """Tracks and reports logging metrics."""
    
    def __init__(self):
        """Initialize metrics tracking."""
        self._lock = threading.RLock()
        self._metrics = {
            "total_logs": 0,
            "total_bytes": 0,
            "level_counts": defaultdict(int),
            "platform_counts": defaultdict(int),
            "status_counts": defaultdict(int),
            "format_counts": defaultdict(int),
            "error_count": 0,
            "last_error": None,
            "last_error_message": None,
            "last_error_time": None,
            "last_rotation": None,
            "start_time": time.time(),
            "last_reset": time.time()
        }
        
    @property
    def total_logs(self) -> int:
        """Get total number of logs."""
        return self._metrics["total_logs"]
        
    @property
    def total_bytes(self) -> int:
        """Get total bytes written."""
        return self._metrics["total_bytes"]
        
    @property
    def error_count(self) -> int:
        """Get error count."""
        return self._metrics["error_count"]
        
    @property
    def last_error(self) -> datetime:
        """Get last error timestamp."""
        return self._metrics["last_error_time"]
        
    @property
    def last_error_message(self) -> str:
        """Get last error message."""
        return self._metrics["last_error"]
        
    @property
    def last_rotation(self) -> datetime:
        """Get last rotation timestamp."""
        return self._metrics["last_rotation"]
        
    @property
    def platform_counts(self) -> Dict[str, int]:
        """Get platform counts."""
        return dict(self._metrics["platform_counts"])
        
    @property
    def level_counts(self) -> Dict[str, int]:
        """Get level counts."""
        return dict(self._metrics["level_counts"])
        
    @property
    def status_counts(self) -> Dict[str, int]:
        """Get status counts."""
        return dict(self._metrics["status_counts"])
        
    @property
    def format_counts(self) -> Dict[str, int]:
        """Get format counts."""
        return dict(self._metrics["format_counts"])
        
    def increment_logs(self, platform: str, level: str, status: str, format_type: str, bytes_written: int) -> None:
        """Increment metrics for a log entry.
        
        Args:
            platform: Platform name
            level: Log level
            status: Status name
            format_type: Format type
            bytes_written: Bytes written
        """
        with self._lock:
            self._metrics["total_logs"] += 1
            self._metrics["total_bytes"] += bytes_written
            self._metrics["level_counts"][level] += 1
            self._metrics["platform_counts"][platform] += 1
            self._metrics["status_counts"][status] += 1
            self._metrics["format_counts"][format_type] += 1
            
    def record_error(self, error: str) -> None:
        """Record an error occurrence.
        
        Args:
            error: Error message
        """
        with self._lock:
            self._metrics["error_count"] += 1
            self._metrics["last_error"] = error
            self._metrics["last_error_message"] = error
            self._metrics["last_error_time"] = datetime.now()
            
    def record_rotation(self) -> None:
        """Record a log rotation."""
        with self._lock:
            self._metrics["last_rotation"] = datetime.now()
            
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics.
        
        Returns:
            dict: Current metrics
        """
        with self._lock:
            metrics = dict(self._metrics)
            
            # Convert defaultdict to regular dict
            metrics["level_counts"] = dict(metrics["level_counts"])
            metrics["platform_counts"] = dict(metrics["platform_counts"])
            metrics["status_counts"] = dict(metrics["status_counts"])
            metrics["format_counts"] = dict(metrics["format_counts"])
            
            # Add computed metrics
            current_time = time.time()
            metrics["uptime"] = current_time - metrics["start_time"]
            metrics["time_since_reset"] = current_time - metrics["last_reset"]
            
            # Add timestamp
            metrics["timestamp"] = datetime.now().isoformat()
            
            return metrics
            
    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._metrics = {
                "total_logs": 0,
                "total_bytes": 0,
                "level_counts": defaultdict(int),
                "platform_counts": defaultdict(int),
                "status_counts": defaultdict(int),
                "format_counts": defaultdict(int),
                "error_count": 0,
                "last_error": None,
                "last_error_message": None,
                "last_error_time": None,
                "last_rotation": None,
                "start_time": self._metrics["start_time"],  # Keep original start time
                "last_reset": time.time()
            } 