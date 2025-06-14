"""Unified metrics and logging system for Dream.OS."""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional, Union, Callable
from functools import wraps
from prometheus_client import Counter, Gauge, Histogram, Summary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Default histogram buckets for latency measurements (in seconds)
DEFAULT_LATENCY_BUCKETS = [0.001, 0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0]

class MetricsManager:
    """Centralized metrics management with Prometheus integration."""
    
    def __init__(self, namespace: str = "dreamos"):
        """Initialize metrics manager.
        
        Args:
            namespace: Metrics namespace prefix
        """
        self.namespace = namespace
        self._counters: Dict[str, Counter] = {}
        self._gauges: Dict[str, Gauge] = {}
        self._histograms: Dict[str, Histogram] = {}
        self._summaries: Dict[str, Summary] = {}
    
    def counter(
        self,
        name: str,
        description: str,
        labels: Optional[list[str]] = None
    ) -> Counter:
        """Get or create a counter metric.
        
        Args:
            name: Metric name
            description: Metric description
            labels: Optional list of label names
            
        Returns:
            Counter: Prometheus counter
        """
        if name not in self._counters:
            self._counters[name] = Counter(
                f"{self.namespace}_{name}",
                description,
                labels or []
            )
        return self._counters[name]
    
    def gauge(
        self,
        name: str,
        description: str,
        labels: Optional[list[str]] = None
    ) -> Gauge:
        """Get or create a gauge metric.
        
        Args:
            name: Metric name
            description: Metric description
            labels: Optional list of label names
            
        Returns:
            Gauge: Prometheus gauge
        """
        if name not in self._gauges:
            self._gauges[name] = Gauge(
                f"{self.namespace}_{name}",
                description,
                labels or []
            )
        return self._gauges[name]
    
    def histogram(
        self,
        name: str,
        description: str,
        labels: Optional[list[str]] = None,
        buckets: Optional[list[float]] = None
    ) -> Histogram:
        """Get or create a histogram metric.
        
        Args:
            name: Metric name
            description: Metric description
            labels: Optional list of label names
            buckets: Optional list of histogram buckets
            
        Returns:
            Histogram: Prometheus histogram
        """
        if name not in self._histograms:
            self._histograms[name] = Histogram(
                f"{self.namespace}_{name}",
                description,
                labels or [],
                buckets=buckets or DEFAULT_LATENCY_BUCKETS
            )
        return self._histograms[name]
    
    def summary(
        self,
        name: str,
        description: str,
        labels: Optional[list[str]] = None
    ) -> Summary:
        """Get or create a summary metric.
        
        Args:
            name: Metric name
            description: Metric description
            labels: Optional list of label names
            
        Returns:
            Summary: Prometheus summary
        """
        if name not in self._summaries:
            self._summaries[name] = Summary(
                f"{self.namespace}_{name}",
                description,
                labels or []
            )
        return self._summaries[name]

class LogManager:
    """Centralized logging management with structured logging."""
    
    def __init__(self, name: str = "dreamos"):
        """Initialize log manager.
        
        Args:
            name: Logger name
        """
        self.logger = logging.getLogger(name)
        self.metrics = MetricsManager(name)
        
        # Common metrics
        self.log_counter = self.metrics.counter(
            "log_total",
            "Total log entries",
            ["level"]
        )
        self.log_latency = self.metrics.histogram(
            "log_latency_seconds",
            "Log processing latency",
            ["level"],
            buckets=DEFAULT_LATENCY_BUCKETS
        )
    
    def _log(
        self,
        level: int,
        msg: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: Optional[Exception] = None
    ):
        """Internal logging method with metrics.
        
        Args:
            level: Logging level
            msg: Log message
            extra: Additional context
            exc_info: Optional exception info
        """
        start_time = time.time()
        
        # Add timestamp if not present
        if extra is None:
            extra = {}
        if "timestamp" not in extra:
            extra["timestamp"] = datetime.utcnow().isoformat()
        
        # Log with context
        self.logger.log(level, msg, extra=extra, exc_info=exc_info)
        
        # Record metrics
        level_name = logging.getLevelName(level).lower()
        self.log_counter.labels(level=level_name).inc()
        self.log_latency.labels(level=level_name).observe(time.time() - start_time)
    
    def debug(self, msg: str, **kwargs):
        """Log debug message."""
        self._log(logging.DEBUG, msg, **kwargs)
    
    def info(self, msg: str, **kwargs):
        """Log info message."""
        self._log(logging.INFO, msg, **kwargs)
    
    def warning(self, msg: str, **kwargs):
        """Log warning message."""
        self._log(logging.WARNING, msg, **kwargs)
    
    def error(self, msg: str, **kwargs):
        """Log error message."""
        self._log(logging.ERROR, msg, **kwargs)
    
    def critical(self, msg: str, **kwargs):
        """Log critical message."""
        self._log(logging.CRITICAL, msg, **kwargs)
    
    def exception(self, msg: str, exc_info: Exception, **kwargs):
        """Log exception with traceback."""
        self._log(logging.ERROR, msg, exc_info=exc_info, **kwargs)

def log_operation(
    operation: str,
    metrics: Optional[Counter] = None,
    duration: Optional[Histogram] = None,
    level: int = logging.INFO
):
    """Decorator for logging operations with metrics.
    
    Args:
        operation: Operation name
        metrics: Optional counter metric to increment
        duration: Optional histogram metric for duration
        level: Logging level
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                if metrics:
                    metrics.inc()
                if duration:
                    duration.observe(time.time() - start_time)
                return result
            except Exception as e:
                logger.exception(f"Error in {operation}")
                raise
        return wrapper
    return decorator

# Global instances
metrics = MetricsManager()
logger = LogManager() 