"""Unified logging manager for Dream.OS."""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field

from ..utils.metrics import metrics, logger, log_operation
from ..utils.exceptions import handle_error

class LogLevel:
    """Log levels with numeric values."""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

# ---------------------------------------------------------------------------
# Compatibility shim: older modules expect ``LogConfig`` to reside in this
# module alongside ``LogManager``.  A lightweight implementation is provided
# here to unblock imports required by the unit-test suite.  It focuses only on
# the attributes that are consumed elsewhere in the code-base (log_dir,
# max_size_mb, max_files, compress_after_days) and can be extended later if
# needed.
# ---------------------------------------------------------------------------
@dataclass
class LogConfig:
    """Lightweight logging configuration container.

    This implementation is intentionally minimal – it just needs to expose the
    attributes that other modules (e.g. the social *LogRotator*) reference.  A
    fuller configuration system can be wired in later without breaking the
    public interface.
    """

    log_dir: str = "./logs"
    max_size_mb: int = 10
    max_files: int = 5
    compress_after_days: int = 7

    # Allow passing arbitrary extra keyword arguments without raising errors –
    # useful when callers supply a superset of settings.
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

        # populate defaults for any missing expected fields
        if not hasattr(self, "log_dir"):
            self.log_dir = "./logs"
        if not hasattr(self, "max_size_mb"):
            self.max_size_mb = 10
        if not hasattr(self, "max_files"):
            self.max_files = 5
        if not hasattr(self, "compress_after_days"):
            self.compress_after_days = 7

class LogManager:
    """Unified logging manager with metrics integration."""
    
    def __init__(self, name: str):
        """Initialize the log manager.
        
        Args:
            name: Name of the logger
        """
        self.name = name
        self._logger = logging.getLogger(name)
        self._metrics = {
            'entries': metrics.counter('log_entries_total', 'Total log entries', ['level']),
            'errors': metrics.counter('log_errors_total', 'Total log errors', ['error_type']),
            'duration': metrics.histogram('log_operation_duration_seconds', 'Log operation duration', ['operation'])
        }
    
    @log_operation('log_debug', metrics='entries', duration='duration')
    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message.
        
        Args:
            message: The message to log
            **kwargs: Additional context
        """
        try:
            self._logger.debug(message, extra=kwargs)
            self._metrics['entries'].labels(level='debug').inc()
        except Exception as e:
            error = handle_error(e, {"operation": "debug", "message": message})
            self._metrics['errors'].labels(error_type=error.__class__.__name__).inc()
            raise
    
    @log_operation('log_info', metrics='entries', duration='duration')
    def info(self, message: str, **kwargs) -> None:
        """Log an info message.
        
        Args:
            message: The message to log
            **kwargs: Additional context
        """
        try:
            self._logger.info(message, extra=kwargs)
            self._metrics['entries'].labels(level='info').inc()
        except Exception as e:
            error = handle_error(e, {"operation": "info", "message": message})
            self._metrics['errors'].labels(error_type=error.__class__.__name__).inc()
            raise
    
    @log_operation('log_warning', metrics='entries', duration='duration')
    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message.
        
        Args:
            message: The message to log
            **kwargs: Additional context
        """
        try:
            self._logger.warning(message, extra=kwargs)
            self._metrics['entries'].labels(level='warning').inc()
        except Exception as e:
            error = handle_error(e, {"operation": "warning", "message": message})
            self._metrics['errors'].labels(error_type=error.__class__.__name__).inc()
            raise
    
    @log_operation('log_error', metrics='entries', duration='duration')
    def error(self, message: str, **kwargs) -> None:
        """Log an error message.
        
        Args:
            message: The message to log
            **kwargs: Additional context
        """
        try:
            self._logger.error(message, extra=kwargs)
            self._metrics['entries'].labels(level='error').inc()
        except Exception as e:
            error = handle_error(e, {"operation": "error", "message": message})
            self._metrics['errors'].labels(error_type=error.__class__.__name__).inc()
            raise
    
    @log_operation('log_critical', metrics='entries', duration='duration')
    def critical(self, message: str, **kwargs) -> None:
        """Log a critical message.
        
        Args:
            message: The message to log
            **kwargs: Additional context
        """
        try:
            self._logger.critical(message, extra=kwargs)
            self._metrics['entries'].labels(level='critical').inc()
        except Exception as e:
            error = handle_error(e, {"operation": "critical", "message": message})
            self._metrics['errors'].labels(error_type=error.__class__.__name__).inc()
            raise
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get logging metrics.
        
        Returns:
            Dictionary of metrics
        """
        return {
            'total_entries': self._metrics['entries']._value.get(),
            'errors': self._metrics['errors']._value.get(),
            'duration': self._metrics['duration']._value.get()
        }
    
    @log_operation('log_shutdown')
    def shutdown(self) -> None:
        """Shutdown the log manager."""
        try:
            for handler in self._logger.handlers[:]:
                handler.close()
                self._logger.removeHandler(handler)
        except Exception as e:
            error = handle_error(e, {"operation": "shutdown"})
            self._metrics['errors'].labels(error_type=error.__class__.__name__).inc()
            raise 
