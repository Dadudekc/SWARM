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

from ..utils.metrics import metrics, logger, log_operation
from ..utils.exceptions import handle_error
from ..utils.file_ops import ensure_dir

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
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_dir: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    metrics_enabled: bool = True

# Default configuration
DEFAULT_CONFIG = LogConfig()

# Metrics
log_metrics = {
    'setup': metrics.counter('log_setup_total', 'Total log setup operations'),
    'errors': metrics.counter('log_config_errors_total', 'Total log configuration errors', ['error_type']),
    'duration': metrics.histogram('log_config_duration_seconds', 'Log configuration duration')
}

@log_operation('setup_logging', metrics=log_metrics['setup'], duration=log_metrics['duration'])
def setup_logging(config: Optional[LogConfig] = None) -> None:
    """Set up logging configuration.
    
    Args:
        config: Optional logging configuration. If not provided, uses default config.
    """
    try:
        if config is None:
            config = DEFAULT_CONFIG
            
        # Create log directory if it doesn't exist
        log_dir = Path(config.log_dir or "logs")
        ensure_dir(log_dir)
        
        # Set up root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(config.level)
        
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
            metrics_dir = log_dir / "metrics"
            ensure_dir(metrics_dir)
            
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
            
        logger.info(
            "logging_setup_complete",
            extra={
                "log_dir": str(log_dir),
                "level": config.level,
                "metrics_enabled": config.metrics_enabled
            }
        )
        
    except Exception as e:
        error = handle_error(e, {"operation": "setup_logging"})
        logger.error(
            "logging_setup_error",
            extra={
                "error": str(error),
                "error_type": error.__class__.__name__
            }
        )
        log_metrics['errors'].labels(error_type=error.__class__.__name__).inc()
        raise

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "level": self.level,
            "format": self.format,
            "log_dir": self.log_dir,
            "max_file_size": self.max_file_size,
            "backup_count": self.backup_count,
            "metrics_enabled": self.metrics_enabled
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogConfig':
        """Create config from dictionary."""
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
            f"metrics_enabled={self.metrics_enabled})"
        )

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"LogConfig(level={self.level}, "
            f"log_dir='{self.log_dir}', "
            f"format='{self.format}', "
            f"max_file_size={self.max_file_size}, "
            f"backup_count={self.backup_count}, "
            f"metrics_enabled={self.metrics_enabled})"
        )

# Constants
METRICS_DIR = "metrics"
DISCORD_WEBHOOK_ENV = "DREAMOS_DISCORD_WEBHOOK"

def get_log_path() -> str:
    """Get path to log directory."""
    return os.path.join(os.getcwd(), DEFAULT_CONFIG.log_dir or DEFAULT_LOG_DIR)

def get_metrics_path() -> str:
    """Get path to metrics directory."""
    return os.path.join(get_log_path(), METRICS_DIR)

def get_retention_date() -> datetime:
    """Get cutoff date for log retention."""
    return datetime.now() - timedelta(days=DEFAULT_MAX_AGE_DAYS)

# Default configuration instance
DEFAULT_CONFIG = LogConfig()

# Constants
METRICS_DIR = "metrics"
DISCORD_WEBHOOK_ENV = "DREAMOS_DISCORD_WEBHOOK"

def get_log_path() -> str:
    """Get path to log directory."""
    return os.path.join(os.getcwd(), DEFAULT_CONFIG.log_dir or DEFAULT_LOG_DIR)

def get_metrics_path() -> str:
    """Get path to metrics directory."""
    return os.path.join(get_log_path(), METRICS_DIR)

def get_retention_date() -> datetime:
    """Get cutoff date for log retention."""
    return datetime.now() - timedelta(days=DEFAULT_MAX_AGE_DAYS)

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
    root_logger.setLevel(config.level)
    
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
        metrics_dir = log_dir / "metrics"
        ensure_dir(metrics_dir)
        
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
