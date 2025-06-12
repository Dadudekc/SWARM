"""Unified logging manager for Dream.OS."""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from ..utils.metrics import metrics, logger, log_operation
from ..utils.exceptions import handle_error

class LogLevel:
    """Log levels with numeric values."""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

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
