"""
Log Manager
---------
Manages logging operations.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os
from pathlib import Path

from dreamos.core.logging.log_config import LogConfig, LogLevel
from dreamos.core.monitoring.metrics import LogMetrics

class LogManager:
    """Manages logging operations."""
    
    def __init__(self, config: Optional[LogConfig] = None):
        """Initialize log manager.
        
        Args:
            config: Optional log configuration
        """
        self._config = config or LogConfig()
        self._metrics = LogMetrics(self._config)
        self._logger = logging.getLogger(self.__class__.__name__)
        self._setup_logging()
        
    def _setup_logging(self):
        """Set up logging configuration."""
        # Create formatter
        formatter = logging.Formatter(self._config.format)
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)
        
        # Add file handler if log_dir specified
        if self._config.log_dir:
            log_dir = Path(self._config.log_dir)
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "dreamos.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)
            
    def debug(self, message: str, **kwargs):
        """Log a debug message.
        
        Args:
            message: The message to log
            **kwargs: Additional context
        """
        self._logger.debug(message, extra=kwargs)
        
    def info(self, message: str, **kwargs):
        """Log an info message.
        
        Args:
            message: The message to log
            **kwargs: Additional context
        """
        self._logger.info(message, extra=kwargs)
        
    def warning(self, message: str, **kwargs):
        """Log a warning message.
        
        Args:
            message: The message to log
            **kwargs: Additional context
        """
        self._logger.warning(message, extra=kwargs)
        
    def error(self, message: str, **kwargs):
        """Log an error message.
        
        Args:
            message: The message to log
            **kwargs: Additional context
        """
        self._logger.error(message, extra=kwargs)
        
    def critical(self, message: str, **kwargs):
        """Log a critical message.
        
        Args:
            message: The message to log
            **kwargs: Additional context
        """
        self._logger.critical(message, extra=kwargs)
        
    def record_metric(self, metric_type: str, value: float, tags: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Record a metric.
        
        Args:
            metric_type: Type of metric
            value: Metric value
            tags: Optional tags
            metadata: Optional metadata
        """
        self._metrics.record_metric(metric_type, value, tags, metadata)
        
    def get_metrics(self, metric_type: Optional[str] = None, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Get metrics with optional filtering.
        
        Args:
            metric_type: Optional metric type to filter by
            start_time: Optional start time to filter by
            end_time: Optional end time to filter by
            
        Returns:
            Dictionary of metric entries
        """
        return self._metrics.get_metrics(metric_type, start_time, end_time)
        
    def get_summary(self, metric_type: Optional[str] = None, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Get metric summary statistics.
        
        Args:
            metric_type: Optional metric type to filter by
            start_time: Optional start time to filter by
            end_time: Optional end time to filter by
            
        Returns:
            Dictionary of summary statistics
        """
        return self._metrics.get_summary(metric_type, start_time, end_time)
        
    def save_metrics(self, filepath: Optional[str] = None) -> None:
        """Save metrics to file.
        
        Args:
            filepath: Optional file path to save to
        """
        self._metrics.save_metrics(filepath)
        
    def load_metrics(self, filepath: Optional[str] = None) -> None:
        """Load metrics from file.
        
        Args:
            filepath: Optional file path to load from
        """
        self._metrics.load_metrics(filepath)
        
    def clear_metrics(self) -> None:
        """Clear all metrics."""
        self._metrics.clear_metrics()

# Create singleton instance
_log_manager = LogManager()

def record_metric(metric_type: str, value: float, tags: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
    """Record a metric.
    
    Args:
        metric_type: Type of metric
        value: Metric value
        tags: Optional tags
        metadata: Optional metadata
    """
    return _log_manager.record_metric(metric_type, value, tags, metadata)

__all__ = [
    'LogManager',
    'LogConfig',
    'LogLevel',
    'record_metric',
    'get_metrics',
    'get_summary',
    'save_metrics',
    'load_metrics',
    'clear_metrics'
] 
