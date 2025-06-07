"""
Logging Utilities
--------------
Core logging configuration and helpers for Dream.OS.
"""

import logging
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union, List

logger = logging.getLogger(__name__)

class PlatformEventLogger:
    """Log platform events with structured data."""
    
    def __init__(
        self,
        log_dir: Union[str, Path],
        platform: str,
        max_events: int = 1000,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize platform event logger.
        
        Args:
            log_dir: Directory for event logs
            platform: Platform name
            max_events: Maximum events to keep in memory
            logger: Optional logger instance
        """
        self.log_dir = Path(log_dir)
        self.platform = platform
        self.max_events = max_events
        self.logger = logger or logging.getLogger(__name__)
        
        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize event storage
        self.events: List[Dict[str, Any]] = []
    
    def log_event(
        self,
        event_type: str,
        status: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> None:
        """Log a platform event.
        
        Args:
            event_type: Type of event
            status: Event status
            message: Event message
            data: Optional event data
            tags: Optional event tags
        """
        event = {
            'timestamp': datetime.now().isoformat(),
            'platform': self.platform,
            'event_type': event_type,
            'status': status,
            'message': message,
            'data': data or {},
            'tags': tags or []
        }
        
        # Add to memory storage
        self.events.append(event)
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]
        
        # Log to file
        log_file = self.log_dir / f"{self.platform}_events.jsonl"
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(event) + '\n')
        except Exception as e:
            self.logger.error(f"Error writing event log: {e}")
        
        # Log to logger
        log_level = logging.INFO if status == 'success' else logging.ERROR
        self.logger.log(
            log_level,
            f"[{self.platform}] {event_type}: {message}",
            extra={'event': event}
        )
    
    def get_events(
        self,
        event_type: Optional[str] = None,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get filtered events.
        
        Args:
            event_type: Filter by event type
            status: Filter by status
            tags: Filter by tags
            limit: Maximum number of events to return
            
        Returns:
            List of matching events
        """
        filtered = self.events
        
        if event_type:
            filtered = [e for e in filtered if e['event_type'] == event_type]
            
        if status:
            filtered = [e for e in filtered if e['status'] == status]
            
        if tags:
            filtered = [e for e in filtered if all(t in e['tags'] for t in tags)]
            
        if limit:
            filtered = filtered[-limit:]
            
        return filtered
    
    def clear_events(self) -> None:
        """Clear all tracked events."""
        self.events.clear()

class StatusTracker:
    """Track platform operation status."""
    
    def __init__(
        self,
        platform: str,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize status tracker.
        
        Args:
            platform: Platform name
            logger: Optional logger instance
        """
        self.platform = platform
        self.logger = logger or logging.getLogger(__name__)
        self.status = {
            'last_operation': None,
            'last_success': None,
            'last_error': None,
            'operation_count': 0,
            'error_count': 0,
            'is_healthy': True
        }
    
    def update_status(
        self,
        operation: str,
        success: bool,
        error: Optional[Exception] = None
    ) -> None:
        """Update platform status.
        
        Args:
            operation: Operation name
            success: Whether operation succeeded
            error: Optional error that occurred
        """
        self.status['last_operation'] = operation
        self.status['operation_count'] += 1
        
        if success:
            self.status['last_success'] = datetime.now().isoformat()
            self.status['is_healthy'] = True
        else:
            self.status['last_error'] = {
                'timestamp': datetime.now().isoformat(),
                'operation': operation,
                'error_type': type(error).__name__ if error else 'Unknown',
                'error_message': str(error) if error else 'Unknown error'
            }
            self.status['error_count'] += 1
            self.status['is_healthy'] = False
            
            if self.logger:
                self.logger.error(
                    f"[{self.platform}] Operation {operation} failed: {error}",
                    extra={'status': self.status}
                )
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status.
        
        Returns:
            Current status dictionary
        """
        return self.status.copy()
    
    def reset_status(self) -> None:
        """Reset status to initial state."""
        self.status = {
            'last_operation': None,
            'last_success': None,
            'last_error': None,
            'operation_count': 0,
            'error_count': 0,
            'is_healthy': True
        }

def configure_logging(
    level: str = "INFO",
    format: str = "%(asctime)s | %(levelname)s | %(message)s",
    log_file: Optional[Path] = None,
    log_dir: Optional[Path] = None
) -> None:
    """Configure logging for the application.
    
    Args:
        level: Logging level
        format: Log message format
        log_file: Optional log file path
        log_dir: Optional log directory
    """
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(format)
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if log file specified
    if log_file:
        if log_dir:
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / log_file
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

def log_platform_event(
    logger: logging.Logger,
    platform: str,
    status: str,
    message: str,
    tags: Optional[list] = None,
    extra: Optional[Dict[str, Any]] = None
) -> None:
    """Log a platform event.
    
    Args:
        logger: Logger instance
        platform: Platform name
        status: Event status
        message: Event message
        tags: Optional tags
        extra: Optional extra data
    """
    log_data = {
        "platform": platform,
        "status": status,
        "message": message,
        "tags": tags or []
    }
    if extra:
        log_data.update(extra)
    
    logger.info(log_data) 