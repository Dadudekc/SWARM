"""
Unified logging configuration for Dream.OS.

This module consolidates all logging-related settings, levels, and configuration
into a single source of truth. It replaces scattered implementations in:
- social/utils/log_level.py
- social/utils/log_config.py
- social/utils/log_metrics.py
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json
import os

class LogLevel(Enum):
    """Standardized log levels for Dream.OS logging system."""
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()

    def should_log(self, threshold: 'LogLevel') -> bool:
        """Check if this level should be logged given the threshold."""
        return self.value >= threshold.value

    @classmethod
    def from_string(cls, level: str) -> 'LogLevel':
        """Convert string to LogLevel enum."""
        try:
            return cls[level.upper()]
        except KeyError:
            raise ValueError(f"Invalid log level: {level}")

@dataclass
class LogConfig:
    """Configuration for logging system."""
    level: LogLevel = LogLevel.INFO
    format: str = "[{timestamp}] [{level}] {message}"
    retention_days: int = 7
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    max_bytes: int = 10 * 1024 * 1024  # 10MB - alias for max_file_size
    backup_count: int = 5
    metrics_enabled: bool = True
    discord_webhook: Optional[str] = None
    log_dir: Optional[str] = None
    platforms: Optional[Dict[str, str]] = None
    batch_size: int = 10
    batch_timeout: float = 1.0
    max_retries: int = 3
    retry_delay: float = 0.5
    backup_dir: Optional[str] = None
    max_age_days: int = 30

    def __post_init__(self):
        """Ensure max_bytes and max_file_size are synchronized."""
        self.max_bytes = self.max_file_size

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "level": self.level.name,
            "format": self.format,
            "retention_days": self.retention_days,
            "max_file_size": self.max_file_size,
            "max_bytes": self.max_bytes,
            "backup_count": self.backup_count,
            "metrics_enabled": self.metrics_enabled,
            "discord_webhook": self.discord_webhook,
            "log_dir": self.log_dir,
            "platforms": self.platforms,
            "batch_size": self.batch_size,
            "batch_timeout": self.batch_timeout,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "backup_dir": self.backup_dir,
            "max_age_days": self.max_age_days
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogConfig':
        """Create config from dictionary."""
        if "level" in data:
            data["level"] = LogLevel.from_string(data["level"])
        return cls(**data)

    def save(self, path: str) -> None:
        """Save config to file."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str) -> 'LogConfig':
        """Load config from file."""
        if not os.path.exists(path):
            return cls()
        with open(path, 'r') as f:
            return cls.from_dict(json.load(f))

# Default configuration
DEFAULT_CONFIG = LogConfig()

# Constants
LOG_DIR = "logs"
METRICS_DIR = "metrics"
DISCORD_WEBHOOK_ENV = "DREAMOS_DISCORD_WEBHOOK"

def get_log_path() -> str:
    """Get path to log directory."""
    return os.path.join(os.getcwd(), LOG_DIR)

def get_metrics_path() -> str:
    """Get path to metrics directory."""
    return os.path.join(get_log_path(), METRICS_DIR)

def get_retention_date() -> datetime:
    """Get cutoff date for log retention."""
    return datetime.now() - timedelta(days=DEFAULT_CONFIG.retention_days) 