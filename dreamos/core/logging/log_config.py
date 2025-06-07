"""
Unified logging configuration for Dream.OS.

This module consolidates all logging-related settings, levels, and configuration
into a single source of truth. It replaces scattered implementations in:
- social/utils/log_level.py
- social/utils/log_config.py
- social/utils/log_metrics.py
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
import json
import os
import logging
import logging.handlers
from pathlib import Path

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

# Default configuration values
DEFAULT_MAX_SIZE_MB = 10
DEFAULT_BATCH_SIZE = 1000
DEFAULT_BATCH_TIMEOUT = 5  # seconds
DEFAULT_MAX_FILES = 5
DEFAULT_ROTATION_CHECK_INTERVAL = 60  # seconds
DEFAULT_CLEANUP_INTERVAL = 3600  # seconds (1 hour)
DEFAULT_COMPRESS_AFTER_DAYS = 7
DEFAULT_LOG_DIR = "logs"
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_MAX_AGE_DAYS = 30
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 0.5

@dataclass
class LogConfig:
    """Configuration for logging system.
    
    This is the unified configuration class that consolidates all logging settings
    across Dream.OS. It supports both simple and advanced logging configurations.
    
    Basic usage:
        config = LogConfig(level=LogLevel.INFO)
        
    Advanced usage:
        config = LogConfig(
            level=LogLevel.DEBUG,
            log_dir="logs",
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            max_file_size=10 * 1024 * 1024,
            backup_count=5,
            max_age_days=7,
            platforms={
                "system": "system.log",
                "agent": "agent.log"
            }
        )
    """
    # Core logging settings
    level: LogLevel = LogLevel.INFO
    format: str = DEFAULT_LOG_FORMAT
    date_format: str = DEFAULT_DATE_FORMAT
    
    # File settings
    log_dir: str = DEFAULT_LOG_DIR
    file_path: Optional[str] = None
    max_file_size: int = DEFAULT_MAX_SIZE_MB * 1024 * 1024  # 10MB in bytes
    max_bytes: int = DEFAULT_MAX_SIZE_MB * 1024 * 1024  # Alias for max_file_size
    backup_count: int = DEFAULT_MAX_FILES
    max_age_days: int = DEFAULT_MAX_AGE_DAYS
    retention_days: int = DEFAULT_MAX_AGE_DAYS  # Alias for max_age_days
    
    # Platform-specific settings
    platforms: Dict[str, str] = field(default_factory=dict)
    
    # Batching settings
    batch_size: int = DEFAULT_BATCH_SIZE
    batch_timeout: float = DEFAULT_BATCH_TIMEOUT
    
    # Maintenance settings
    rotation_check_interval: float = DEFAULT_ROTATION_CHECK_INTERVAL
    cleanup_interval: float = DEFAULT_CLEANUP_INTERVAL
    compress_after_days: int = DEFAULT_COMPRESS_AFTER_DAYS
    
    # Optional features
    metrics_enabled: bool = True
    discord_webhook: Optional[str] = None
    discord_enabled: bool = False
    discord_levels: List[str] = field(default_factory=list)
    
    # Error handling
    max_retries: int = DEFAULT_MAX_RETRIES
    retry_delay: float = DEFAULT_RETRY_DELAY
    
    # Output control
    log_to_console: bool = True
    log_to_file: bool = True
    
    def __post_init__(self):
        """Validate and normalize configuration after initialization."""
        # Ensure max_bytes and max_file_size are synchronized
        self.max_bytes = self.max_file_size
        
        # Create log directory if it doesn't exist
        if self.log_dir:
            os.makedirs(self.log_dir, exist_ok=True)
            
        # Set default file path if not specified
        if self.log_to_file and not self.file_path:
            self.file_path = os.path.join(self.log_dir, "system.log")
            
        # Validate numeric values
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if self.batch_timeout <= 0:
            raise ValueError("batch_timeout must be positive")
        if self.max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        if self.retry_delay < 0:
            raise ValueError("retry_delay cannot be negative")
        if self.max_age_days <= 0:
            raise ValueError("max_age_days must be positive")
        if self.compress_after_days <= 0:
            raise ValueError("compress_after_days must be positive")
        if self.rotation_check_interval <= 0:
            raise ValueError("rotation_check_interval must be positive")
        if self.cleanup_interval <= 0:
            raise ValueError("cleanup_interval must be positive")

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "level": self.level.name,
            "format": self.format,
            "date_format": self.date_format,
            "log_dir": self.log_dir,
            "file_path": self.file_path,
            "max_file_size": self.max_file_size,
            "max_bytes": self.max_bytes,
            "backup_count": self.backup_count,
            "max_age_days": self.max_age_days,
            "retention_days": self.retention_days,
            "platforms": self.platforms,
            "batch_size": self.batch_size,
            "batch_timeout": self.batch_timeout,
            "rotation_check_interval": self.rotation_check_interval,
            "cleanup_interval": self.cleanup_interval,
            "compress_after_days": self.compress_after_days,
            "metrics_enabled": self.metrics_enabled,
            "discord_webhook": self.discord_webhook,
            "discord_enabled": self.discord_enabled,
            "discord_levels": self.discord_levels,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "log_to_console": self.log_to_console,
            "log_to_file": self.log_to_file
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

    def __str__(self) -> str:
        """String representation."""
        return (
            f"LogConfig(level={self.level}, "
            f"log_dir='{self.log_dir}', "
            f"format='{self.format}', "
            f"max_file_size={self.max_file_size}, "
            f"backup_count={self.backup_count}, "
            f"platforms={self.platforms})"
        )

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"LogConfig(level={self.level}, "
            f"log_dir='{self.log_dir}', "
            f"format='{self.format}', "
            f"date_format='{self.date_format}', "
            f"file_path='{self.file_path}', "
            f"max_file_size={self.max_file_size}, "
            f"backup_count={self.backup_count}, "
            f"max_age_days={self.max_age_days}, "
            f"platforms={self.platforms}, "
            f"batch_size={self.batch_size}, "
            f"batch_timeout={self.batch_timeout}, "
            f"rotation_check_interval={self.rotation_check_interval}, "
            f"cleanup_interval={self.cleanup_interval}, "
            f"compress_after_days={self.compress_after_days}, "
            f"metrics_enabled={self.metrics_enabled}, "
            f"discord_webhook={self.discord_webhook}, "
            f"discord_enabled={self.discord_enabled}, "
            f"discord_levels={self.discord_levels}, "
            f"max_retries={self.max_retries}, "
            f"retry_delay={self.retry_delay}, "
            f"log_to_console={self.log_to_console}, "
            f"log_to_file={self.log_to_file})"
        )

# Default configuration instance
DEFAULT_CONFIG = LogConfig()

# Constants
METRICS_DIR = "metrics"
DISCORD_WEBHOOK_ENV = "DREAMOS_DISCORD_WEBHOOK"

def get_log_path() -> str:
    """Get path to log directory."""
    return os.path.join(os.getcwd(), DEFAULT_CONFIG.log_dir)

def get_metrics_path() -> str:
    """Get path to metrics directory."""
    return os.path.join(get_log_path(), METRICS_DIR)

def get_retention_date() -> datetime:
    """Get cutoff date for log retention."""
    return datetime.now() - timedelta(days=DEFAULT_CONFIG.retention_days)

def setup_logging(config: Optional[LogConfig] = None) -> None:
    """Set up logging configuration.
    
    Args:
        config: Optional logging configuration. If not provided, uses default config.
    """
    if config is None:
        config = DEFAULT_CONFIG
        
    # Create log directory if it doesn't exist
    log_dir = Path(config.log_dir or get_log_path())
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(config.level.name)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add file handler
    log_file = log_dir / "dreamos.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=config.max_file_size,
        backupCount=config.backup_count
    )
    file_handler.setFormatter(logging.Formatter(config.format))
    root_logger.addHandler(file_handler)
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(config.format))
    root_logger.addHandler(console_handler)
    
    # Set up metrics logging if enabled
    if config.metrics_enabled:
        metrics_dir = Path(get_metrics_path())
        metrics_dir.mkdir(parents=True, exist_ok=True)
        
        metrics_logger = logging.getLogger("metrics")
        metrics_logger.setLevel(logging.INFO)
        
        metrics_file = metrics_dir / "metrics.log"
        metrics_handler = logging.handlers.RotatingFileHandler(
            metrics_file,
            maxBytes=config.max_file_size,
            backupCount=config.backup_count
        )
        metrics_handler.setFormatter(logging.Formatter(config.format))
        metrics_logger.addHandler(metrics_handler) 