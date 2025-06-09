"""
Log Manager
----------
Manages logging for social media operations.
"""

import logging
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
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
    
    def __init__(self, config: Optional[BaseLogConfig] = None):
        """Initialize log manager.
        
        Args:
            config: Optional log configuration
        """
        if self._initialized:
            return
            
        self.config = config or BaseLogConfig()
        self.logger = logging.getLogger("social")
        self.logger.setLevel(self.config.level.value)
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(self.config.format))
        self.logger.addHandler(console_handler)
        
        # Add file handler if specified
        if self.config.file_path:
            file_handler = RotatingFileHandler(
                self.config.file_path,
                maxBytes=self.config.max_bytes,
                backupCount=self.config.backup_count
            )
            file_handler.setFormatter(logging.Formatter(self.config.format))
            self.logger.addHandler(file_handler)
        
        self._metrics = {
            'total_entries': 0,
            'entries_by_level': {},
            'entries_by_platform': {},
            'errors': 0
        }
        
        rotation_config = RotationConfig(
            max_size_mb=self.config.max_size_mb,
            max_files=self.config.max_files,
            max_age_days=self.config.compress_after_days,
            backup_dir=self.config.log_dir,
            max_bytes=self.config.max_bytes
        )
        self._rotator = LogRotator(rotation_config)
        self.pipeline = LogPipeline(self.config)
        self._setup_logging()
        self._initialized = True

    def set_level(self, level: LogLevel) -> None:
        """Dynamically update the log level for all handlers."""
        self.config.level = level
        self.logger.setLevel(level.value)
        for handler in self.logger.handlers:
            handler.setLevel(level.value)
    
    def _setup_logging(self):
        """Set up logging configuration."""
        self.logger.setLevel(self.config.level.value)

        self._handlers: Dict[str, RotatingFileHandler] = {}
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create formatter
        formatter = logging.Formatter(
            self.config.format,
        )
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Add file handlers for each platform
        log_dir = Path(self.config.log_dir)
        log_dir.mkdir(exist_ok=True)
        
        for platform, log_file in self.config.platforms.items():
            file_handler = RotatingFileHandler(
                log_dir / log_file,
                maxBytes=self.config.max_bytes,
                backupCount=self.config.backup_count
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            self._handlers[platform] = file_handler
    
    def write_log(self, platform: str, message: str, level: LogLevel = LogLevel.INFO, **kwargs) -> None:
        """Write a log entry."""
        try:
            # Update metrics
            self._metrics['total_entries'] += 1
            self._metrics['entries_by_level'][level] = self._metrics['entries_by_level'].get(level, 0) + 1
            self._metrics['entries_by_platform'][platform] = self._metrics['entries_by_platform'].get(platform, 0) + 1
            
            # Log message
            logger = logging.getLogger(f"dreamos.social.{platform}")
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "level": level.value,
                "message": message,
                "platform": platform,
                **kwargs
            }
            
            # Add to pipeline
            self.pipeline.add_entry(log_entry)
            
            # Log to file
            log_method = getattr(logger, level.value.lower())
            log_method(message)
            
        except Exception as e:
            self._metrics['errors'] += 1
            logging.error(f"Error writing log: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        metrics = {
            "total_entries": self._metrics['total_entries'],
            "platforms": {}
        }
        
        for platform, log_file in self.config.platforms.items():
            if log_file.exists():
                size = log_file.stat().st_size
                entries = len(self.read_logs(platform))
                metrics["platforms"][platform] = {
                    "size_bytes": size,
                    "entries": entries
                }
        
        return metrics
    
    def read_logs(self, platform: str, level: Optional[LogLevel] = None) -> List[Dict[str, Any]]:
        """Read logs for a platform.
        
        Args:
            platform: Platform name
            level: Optional log level filter
            
        Returns:
            List of log entries
        """
        log_file = self.config.get_platform_log(platform)
        if not log_file or not log_file.exists():
            return []
            
        entries = []
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if level is None or entry.get("level") == level.value:
                        entries.append(entry)
                except json.JSONDecodeError:
                    continue
        return entries
    
    def cleanup(self) -> None:
        """Clean up old log files."""
        try:
            log_dir = Path(self.config.log_dir)
            max_age_days = self.config.max_age_days
            cutoff = None
            if max_age_days > 0:
                cutoff = datetime.now() - timedelta(days=max_age_days)

            for pattern in self.config.platforms.values():
                stem = Path(pattern).stem
                suffix = Path(pattern).suffix
                backups = sorted(
                    list(log_dir.glob(f"{stem}_*{suffix}")) +
                    list(log_dir.glob(f"{stem}{suffix}.*")),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True,
                )

                # Determine which files to keep
                keep = set(backups[: max(0, self.config.backup_count - 1)])

                for file_path in backups[max(0, self.config.backup_count - 1):]:
                    try:
                        file_path.unlink()
                    except Exception:
                        pass

                if cutoff:
                    for file_path in keep:
                        try:
                            if file_path.stat().st_mtime < cutoff.timestamp():
                                file_path.unlink()
                        except Exception:
                            pass
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")

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
        self.logger.removeHandler(handler)

        log_file = Path(handler.baseFilename)

        rotated_path = self._rotator.rotate(str(log_file))

        # Recreate handler after rotation
        new_handler = RotatingFileHandler(
            log_file,
            maxBytes=self.config.max_bytes,
            backupCount=self.config.backup_count,
        )
        formatter = logging.Formatter(
            self.config.format,
        )
        new_handler.setFormatter(formatter)
        self.logger.addHandler(new_handler)
        self._handlers[platform] = new_handler

        return rotated_path
    
    def debug(self, platform: str, message: str, **kwargs) -> None:
        """Write debug log entry."""
        self.write_log(platform=platform, message=message, level="DEBUG", **kwargs)
    
    def info(self, platform: str, message: str, **kwargs) -> None:
        """Write info log entry."""
        self.write_log(platform=platform, message=message, level="INFO", **kwargs)
    
    def warning(self, platform: str, message: str, **kwargs) -> None:
        """Write warning log entry."""
        self.write_log(platform=platform, message=message, level="WARNING", **kwargs)
    
    def error(self, platform: str, message: str, **kwargs) -> None:
        """Write error log entry."""
        self.write_log(platform=platform, message=message, level="ERROR", **kwargs)
    
    def critical(self, platform: str, message: str, **kwargs) -> None:
        """Write critical log entry."""
        self.write_log(platform=platform, message=message, level="CRITICAL", **kwargs)
