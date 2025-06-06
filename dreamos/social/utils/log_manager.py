"""
Simplified Log Manager
--------------------
Provides centralized logging with basic rotation and metrics.
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
    """Log levels."""
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

@dataclass
class LogConfig:
    """Log configuration."""
    level: LogLevel = LogLevel.INFO
    log_dir: str = "logs"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    max_age_days: int = 30
    platforms: Dict[str, str] = None
    
    def __post_init__(self):
        if self.platforms is None:
            self.platforms = {
                "system": "system.log",
                "discord": "discord.log",
                "voice": "voice.log",
                "agent": "agent.log"
            }

class LogManager:
    """Simplified log manager implementation."""
    
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
        if self._initialized:
            return
            
        self._config = config or LogConfig()
        self._metrics = {
            'total_entries': 0,
            'entries_by_level': {},
            'entries_by_platform': {},
            'errors': 0
        }
        rotation_config = RotationConfig(
            max_size_mb=max(1, self._config.max_bytes // (1024 * 1024)),
            max_files=self._config.backup_count,
            max_age_days=self._config.max_age_days,
            backup_dir=str(Path(self._config.log_dir) / "backups"),
            max_bytes=self._config.max_bytes,
        )
        self._rotator = LogRotator(rotation_config)
        self._setup_logging()
        self._initialized = True

    def set_level(self, level: LogLevel) -> None:
        """Dynamically update the log level for all handlers."""
        self._config.level = level
        root_logger = logging.getLogger()
        root_logger.setLevel(level.value)
        for handler in root_logger.handlers:
            handler.setLevel(level.value)
    
    def _setup_logging(self):
        """Set up logging configuration."""
        root_logger = logging.getLogger()
        root_logger.setLevel(self._config.level.value)

        self._handlers: Dict[str, RotatingFileHandler] = {}
        
        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Create formatter
        formatter = logging.Formatter(
            self._config.log_format,
            self._config.date_format
        )
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # Add file handlers for each platform
        log_dir = Path(self._config.log_dir)
        log_dir.mkdir(exist_ok=True)
        
        for platform, log_file in self._config.platforms.items():
            file_handler = RotatingFileHandler(
                log_dir / log_file,
                maxBytes=self._config.max_bytes,
                backupCount=self._config.backup_count
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            self._handlers[platform] = file_handler
    
    def write_log(self, message: str, level: str = "INFO", platform: str = "system", **kwargs) -> None:
        """Write a log entry."""
        try:
            # Update metrics
            self._metrics['total_entries'] += 1
            self._metrics['entries_by_level'][level] = self._metrics['entries_by_level'].get(level, 0) + 1
            self._metrics['entries_by_platform'][platform] = self._metrics['entries_by_platform'].get(platform, 0) + 1
            
            # Get logger for platform
            logger = logging.getLogger(platform)
            
            # Log message
            log_method = getattr(logger, level.lower(), logger.info)
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
            log_dir = Path(self._config.log_dir)
            entries = []
            
            # Get log file for platform
            if platform and platform not in self._config.platforms:
                raise ValueError(f"Invalid platform: {platform}")
                
            log_file = log_dir / self._config.platforms[platform]
            
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
            log_dir = Path(self._config.log_dir)
            max_age_days = self._config.max_age_days
            
            if max_age_days > 0:
                cutoff = datetime.now() - timedelta(days=max_age_days)
                for log_file in log_dir.glob('*.log*'):
                    try:
                        if log_file.stat().st_mtime < cutoff.timestamp():
                            log_file.unlink()
                    except Exception as e:
                        logging.error(f"Error removing old log file {log_file}: {e}")
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")

    def rotate(self, platform: str) -> Optional[str]:
        """Rotate the log file for a given platform."""
        if platform not in self._config.platforms:
            raise ValueError(f"Invalid platform: {platform}")

        handler = self._handlers.get(platform)
        if not handler:
            return None

        # Ensure handler is flushed and closed before rotation
        handler.flush()
        handler.close()
        logging.getLogger().removeHandler(handler)

        log_file = Path(handler.baseFilename)

        rotated_path = self._rotator.rotate(str(log_file))

        # Recreate handler after rotation
        new_handler = RotatingFileHandler(
            log_file,
            maxBytes=self._config.max_bytes,
            backupCount=self._config.backup_count,
        )
        formatter = logging.Formatter(
            self._config.log_format,
            self._config.date_format,
        )
        new_handler.setFormatter(formatter)
        logging.getLogger().addHandler(new_handler)
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