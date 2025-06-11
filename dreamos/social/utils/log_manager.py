"""
Log Manager
----------
Manages logging for social media operations.
"""

import logging
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, timedelta
import threading
from logging.handlers import RotatingFileHandler
from dataclasses import dataclass
from enum import Enum

from .log_rotator import LogRotator
from .log_types import RotationConfig
from .log_config import LogConfig as BaseLogConfig, LogLevel
from .log_pipeline import LogPipeline

__all__ = [
    'LogLevel',
    'LogEntry',
    'LogConfig',
    'LogManager',
    'set_level',
    '_setup_logging',
    'write_log',
    'get_metrics',
    'read_logs',
    'cleanup',
    'rotate',
    'debug',
    'info',
    'warning',
    'error',
    'critical'
]

@dataclass
class LogEntry:
    """Represents a log entry."""
    timestamp: datetime
    level: str
    platform: str
    message: str
    tags: List[str] = None
    metadata: Dict[str, Any] = None

class LogManager:
    """Manages logging for social media operations."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, config: Optional[BaseLogConfig] = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, log_dir: Union[str, Path, BaseLogConfig]):
        """Initialize the log manager.
        
        Args:
            log_dir: Either a LogConfig object or path to log directory
        """
        if self._initialized:
            return
            
        if isinstance(log_dir, (str, Path)):
            self.config = BaseLogConfig(log_dir=str(log_dir))
            self.log_dir = str(log_dir)  # Legacy compatibility
        else:
            self.config = log_dir
            self.log_dir = log_dir.log_dir  # Legacy compatibility
            
        self._pipeline = LogPipeline(self.config)
        self._logger = logging.getLogger(__name__)
        self._metrics = {
            "total_entries": 0,
            "entries_by_level": {},
            "entries_by_platform": {},
            "last_update": datetime.now()
        }
        
        self._setup_logging()
        self._initialized = True

    def _setup_logging(self):
        """Set up logging configuration."""
        formatter = logging.Formatter(self.config.format)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)
        
        # File handler
        file_handler = logging.FileHandler(os.path.join(self.config.log_dir, "app.log"))
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)

    @property
    def logger(self) -> logging.Logger:
        """Get the logger instance."""
        return self._logger

    def write_log(self, message: str, level: Union[str, LogLevel] = LogLevel.INFO, platform: str = "default", **kwargs) -> None:
        """Write a log entry.
        
        Args:
            message: Message to log
            level: Log level (string or LogLevel)
            platform: Platform name
            **kwargs: Additional log data
        """
        try:
            # Convert string level to LogLevel if needed
            if isinstance(level, str):
                level = LogLevel.from_str(level)
                
            entry = LogEntry(
                message=message,
                level=level,
                platform=platform,
                metadata=kwargs
            )
            self._pipeline.add_entry(entry)
            self._update_metrics(entry)
        except Exception as e:
            self._logger.error(f"Error writing log: {e}")

    def _update_metrics(self, entry: LogEntry) -> None:
        """Update metrics with a new entry."""
        try:
            self._metrics["total_entries"] += 1
            
            # Update entries by level
            level_name = entry.level.name
            if level_name not in self._metrics["entries_by_level"]:
                self._metrics["entries_by_level"][level_name] = 0
            self._metrics["entries_by_level"][level_name] += 1
            
            # Update entries by platform
            if entry.platform not in self._metrics["entries_by_platform"]:
                self._metrics["entries_by_platform"][entry.platform] = 0
            self._metrics["entries_by_platform"][entry.platform] += 1
            
            self._metrics["last_update"] = datetime.now()
        except Exception as e:
            self._logger.error(f"Error updating metrics: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics.
        
        Returns:
            Dictionary with metrics
        """
        return self._metrics.copy()

    def read_logs(self, platform: Optional[str] = None, level: Optional[LogLevel] = None, limit: Optional[int] = None) -> List[LogEntry]:
        """Read logs from the specified platform."""
        return self._pipeline.read_logs(platform, level, limit)

    def cleanup(self) -> None:
        """Clean up resources."""
        self._pipeline.stop()

    def __del__(self):
        """Cleanup on deletion."""
        self.cleanup()

    def set_level(self, level: LogLevel) -> None:
        """Set the logging level."""
        self._logger.setLevel(level.value)

    def debug(self, platform: str, message: str, **kwargs) -> None:
        """Log a debug message."""
        self.write_log(message, LogLevel.DEBUG, platform, **kwargs)

    def info(self, platform: str, message: str, **kwargs) -> None:
        """Log an info message."""
        self.write_log(message, LogLevel.INFO, platform, **kwargs)

    def warning(self, platform: str, message: str, **kwargs) -> None:
        """Log a warning message."""
        self.write_log(message, LogLevel.WARNING, platform, **kwargs)

    def error(self, platform: str, message: str, **kwargs) -> None:
        """Log an error message."""
        self.write_log(message, LogLevel.ERROR, platform, **kwargs)

    def critical(self, platform: str, message: str, **kwargs) -> None:
        """Log a critical message."""
        self.write_log(message, LogLevel.CRITICAL, platform, **kwargs)

    def rotate(self, platform: str) -> Optional[str]:
        """Rotate the log file for a given platform."""
        if platform not in self.config.platforms:
            raise ValueError(f"Invalid platform: {platform}")

        handler = self._handlers.get(platform)
        if not handler:
            return None

        # Ensure handler is flushed and closed before rotation
        handler.flush()
        handler.close()
        self._logger.removeHandler(handler)

        log_file = Path(handler.baseFilename)

        rotated_path = self._rotator.rotate(str(log_file))

        # Recreate handler after rotation
        new_handler = RotatingFileHandler(
            log_file,
            maxBytes=self.config.max_bytes,
            backupCount=self.config.max_files,
        )
        formatter = logging.Formatter(
            self.config.format,
        )
        new_handler.setFormatter(formatter)
        self._logger.addHandler(new_handler)
        self._handlers[platform] = new_handler

        return rotated_path
