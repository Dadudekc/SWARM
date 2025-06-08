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

class LogLevel(Enum):
    """Log levels for social media operations."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

@dataclass
class LogEntry:
    """Represents a log entry."""
    timestamp: datetime
    level: str
    platform: str
    message: str
    tags: List[str] = None
    metadata: Dict[str, Any] = None

class LogConfig:
    """Configuration for logging."""
    
    def __init__(self, 
                 level: LogLevel = LogLevel.INFO,
                 format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                 file: Optional[str] = None):
        """Initialize log configuration.
        
        Args:
            level: Log level
            format: Log format string
            file: Optional log file path
        """
        self.level = level
        self.format = format
        self.file = file

class LogManager:
    """Manages logging for social media operations."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, config: Optional[LogConfig] = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config: Optional[LogConfig] = None):
        """Initialize log manager.
        
        Args:
            config: Optional log configuration
        """
        if self._initialized:
            return
            
        self.config = config or LogConfig()
        self.logger = logging.getLogger("social")
        self.logger.setLevel(self.config.level.value)
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(self.config.format))
        self.logger.addHandler(console_handler)
        
        # Add file handler if specified
        if self.config.file:
            file_handler = logging.FileHandler(self.config.file)
            file_handler.setFormatter(logging.Formatter(self.config.format))
            self.logger.addHandler(file_handler)
        
        self._metrics = {
            'total_entries': 0,
            'entries_by_level': {},
            'entries_by_platform': {},
            'errors': 0
        }
        rotation_config = RotationConfig(
            max_size_mb=max(1, self.config.max_bytes // (1024 * 1024)),
            max_files=self.config.backup_count,
            max_age_days=self.config.max_age_days,
            # Let LogRotator manage the "backups" directory itself. Passing the
            # base log directory avoids creating nested "backups/backups" paths.
            backup_dir=str(self.config.log_dir),
            max_bytes=self.config.max_bytes,
        )
        self._rotator = LogRotator(rotation_config)
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
    
    def write_log(self, message: str, level: str = "INFO", platform: str = "system", **kwargs) -> None:
        """Write a log entry."""
        try:
            # Update metrics
            self._metrics['total_entries'] += 1
            self._metrics['entries_by_level'][level] = self._metrics['entries_by_level'].get(level, 0) + 1
            self._metrics['entries_by_platform'][platform] = self._metrics['entries_by_platform'].get(platform, 0) + 1
            
            # Log message
            log_method = getattr(self.logger, level.lower(), self.logger.info)
            log_method(message, extra=kwargs)
            
        except Exception as e:
            self._metrics['errors'] += 1
            logging.error(f"Error writing log: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return dict(self._metrics)
    
    def read_logs(
        self,
        platform: Optional[str] = None,
        level: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Read log entries with optional filtering."""
        try:
            log_dir = Path(self.config.log_dir)
            entries = []
            
            # Get log file for platform
            if platform and platform not in self.config.platforms:
                raise ValueError(f"Invalid platform: {platform}")
                
            log_file = log_dir / self.config.platforms[platform]
            
            # Read and parse log file
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if isinstance(entry, dict):
                            # Apply filters
                            if level and entry.get("level") != level:
                                continue
                            if start_time and datetime.fromisoformat(entry.get("timestamp", "")) < start_time:
                                continue
                            if end_time and datetime.fromisoformat(entry.get("timestamp", "")) > end_time:
                                continue
                            entries.append(entry)
                    except json.JSONDecodeError:
                        continue
            
            # Apply limit
            if limit is not None:
                entries = entries[-limit:]
                
            return entries
            
        except Exception as e:
            logging.error(f"Error reading logs: {e}")
            return []
    
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
        self.write_log(message=message, level="DEBUG", platform=platform, **kwargs)
    
    def info(self, platform: str, message: str, **kwargs) -> None:
        """Write info log entry."""
        self.write_log(message=message, level="INFO", platform=platform, **kwargs)
    
    def warning(self, platform: str, message: str, **kwargs) -> None:
        """Write warning log entry."""
        self.write_log(message=message, level="WARNING", platform=platform, **kwargs)
    
    def error(self, platform: str, message: str, **kwargs) -> None:
        """Write error log entry."""
        self.write_log(message=message, level="ERROR", platform=platform, **kwargs)
    
    def critical(self, platform: str, message: str, **kwargs) -> None:
        """Write critical log entry."""
        self.write_log(message=message, level="CRITICAL", platform=platform, **kwargs)
