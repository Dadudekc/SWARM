"""
Log Metrics Module
-----------------
Tracks and aggregates logging metrics.
"""

from typing import Dict, Any, Optional, List, Deque
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading
import logging
import time
from dataclasses import dataclass
from statistics import mean, median, stdev

logger = logging.getLogger(__name__)

@dataclass
class OperationTime:
    """Represents a timed operation."""
    operation: str
    duration: float
    timestamp: datetime

@dataclass
class RetryAttempt:
    """Represents a retry attempt."""
    operation: str
    attempt: int
    success: bool
    timestamp: datetime
    error: Optional[str] = None

class LogMetrics:
    """Tracks and aggregates logging metrics."""
    
    def __init__(
        self,
        window_size: int = 1000,
        max_operation_times: int = 1000,
        max_retry_history: int = 1000
    ):
        """Initialize metrics tracking.
        
        Args:
            window_size: Size of rolling window for rate calculations
            max_operation_times: Maximum number of operation times to keep
            max_retry_history: Maximum number of retry attempts to keep
        """
        self._lock = threading.Lock()
        self.window_size = window_size
        self.max_operation_times = max_operation_times
        self.max_retry_history = max_retry_history
        
        # Basic metrics
        self.total_logs = 0
        self.total_bytes = 0
        self.error_count = 0
        self.last_error = None
        self.last_error_time = None
        
        # Counts by category
        self.platform_counts = defaultdict(int)
        self.level_counts = defaultdict(int)
        self.status_counts = defaultdict(int)
        self.format_counts = defaultdict(int)
        
        # Operation timing with rolling window
        self.operation_times: Deque[OperationTime] = deque(maxlen=max_operation_times)
        self.retry_history: Deque[RetryAttempt] = deque(maxlen=max_retry_history)
        
        # Rate tracking
        self.log_timestamps: Deque[datetime] = deque(maxlen=window_size)
        self.error_timestamps: Deque[datetime] = deque(maxlen=window_size)
    
    def increment_logs(
        self,
        platform: str,
        level: str = "INFO",
        status: str = "success",
        format_type: str = "json",
        size: int = 0
    ) -> None:
        """Increment log counts with thread safety.
        
        Args:
            platform: Platform name
            level: Log level
            status: Operation status
            format_type: Log format
            size: Log size in bytes
        """
        with self._lock:
            try:
                self.total_logs += 1
                self.total_bytes += size
                
                self.platform_counts[platform] += 1
                self.level_counts[level] += 1
                self.status_counts[status] += 1
                self.format_counts[format_type] += 1
                
                # Update rate tracking
                self.log_timestamps.append(datetime.now())
            except Exception as e:
                logger.error(f"Error incrementing logs: {str(e)}")
    
    def record_error(self, error: str) -> None:
        """Record an error with thread safety.
        
        Args:
            error: Error message
        """
        with self._lock:
            try:
                self.error_count += 1
                self.last_error = error
                self.last_error_time = datetime.now()
                
                # Update rate tracking
                self.error_timestamps.append(self.last_error_time)
            except Exception as e:
                logger.error(f"Error recording error: {str(e)}")
    
    def record_operation_time(self, operation: str, duration: float) -> None:
        """Record operation timing with thread safety.
        
        Args:
            operation: Operation name
            duration: Duration in seconds
        """
        with self._lock:
            try:
                self.operation_times.append(OperationTime(
                    operation=operation,
                    duration=duration,
                    timestamp=datetime.now()
                ))
            except Exception as e:
                logger.error(f"Error recording operation time: {str(e)}")
    
    def record_retry(
        self,
        operation: str,
        attempt: int,
        success: bool,
        error: Optional[str] = None
    ) -> None:
        """Record retry attempt with thread safety.
        
        Args:
            operation: Operation name
            attempt: Attempt number
            success: Whether attempt succeeded
            error: Optional error message
        """
        with self._lock:
            try:
                self.retry_history.append(RetryAttempt(
                    operation=operation,
                    attempt=attempt,
                    success=success,
                    timestamp=datetime.now(),
                    error=error
                ))
            except Exception as e:
                logger.error(f"Error recording retry: {str(e)}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics with thread safety.
        
        Returns:
            Dict containing metrics
        """
        with self._lock:
            try:
                # Calculate rates
                current_time = datetime.now()
                log_rate = self._calculate_rate(self.log_timestamps, current_time)
                error_rate = self._calculate_rate(self.error_timestamps, current_time)
                
                # Calculate operation statistics
                op_stats = self._calculate_operation_stats()
                
                return {
                    "total_logs": self.total_logs,
                    "total_bytes": self.total_bytes,
                    "error_count": self.error_count,
                    "last_error": self.last_error,
                    "last_error_time": self.last_error_time,
                    "platform_counts": dict(self.platform_counts),
                    "level_counts": dict(self.level_counts),
                    "status_counts": dict(self.status_counts),
                    "format_counts": dict(self.format_counts),
                    "log_rate": log_rate,
                    "error_rate": error_rate,
                    "operation_stats": op_stats,
                    "retry_stats": self._calculate_retry_stats()
                }
            except Exception as e:
                logger.error(f"Error getting metrics: {str(e)}")
                return {}
    
    def _calculate_rate(self, timestamps: Deque[datetime], current_time: datetime) -> float:
        """Calculate rate of events per second.
        
        Args:
            timestamps: Queue of event timestamps
            current_time: Current time
            
        Returns:
            Events per second
        """
        if not timestamps:
            return 0.0
        
        window_start = current_time - timedelta(seconds=60)  # 1-minute window
        recent_events = sum(1 for ts in timestamps if ts >= window_start)
        return recent_events / 60.0  # events per second
    
    def _calculate_operation_stats(self) -> Dict[str, Any]:
        """Calculate statistics for operations.
        
        Returns:
            Dict containing operation statistics
        """
        if not self.operation_times:
            return {}
        
        durations = [op.duration for op in self.operation_times]
        return {
            "count": len(durations),
            "mean": mean(durations),
            "median": median(durations),
            "stdev": stdev(durations) if len(durations) > 1 else 0.0,
            "min": min(durations),
            "max": max(durations)
        }
    
    def _calculate_retry_stats(self) -> Dict[str, Any]:
        """Calculate statistics for retry attempts.
        
        Returns:
            Dict containing retry statistics
        """
        if not self.retry_history:
            return {}
        
        total_retries = len(self.retry_history)
        successful_retries = sum(1 for r in self.retry_history if r.success)
        
        return {
            "total_retries": total_retries,
            "successful_retries": successful_retries,
            "retry_success_rate": successful_retries / total_retries if total_retries > 0 else 0.0
        }
    
    def reset(self) -> None:
        """Reset all metrics with thread safety."""
        with self._lock:
            try:
                self.total_logs = 0
                self.total_bytes = 0
                self.error_count = 0
                self.last_error = None
                self.last_error_time = None
                
                self.platform_counts.clear()
                self.level_counts.clear()
                self.status_counts.clear()
                self.format_counts.clear()
                
                self.operation_times.clear()
                self.retry_history.clear()
                
                self.log_timestamps.clear()
                self.error_timestamps.clear()
            except Exception as e:
                logger.error(f"Error resetting metrics: {str(e)}") 