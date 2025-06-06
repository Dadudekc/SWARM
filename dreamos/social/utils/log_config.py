"""Logging configuration for the social media platform."""

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

class LogLevel(Enum):
    """Log levels for the application."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

# Default configuration values
DEFAULT_MAX_SIZE_MB = 10
DEFAULT_BATCH_SIZE = 1000
DEFAULT_BATCH_TIMEOUT = 5  # seconds
DEFAULT_MAX_FILES = 5
DEFAULT_ROTATION_CHECK_INTERVAL = 60  # seconds
DEFAULT_CLEANUP_INTERVAL = 3600  # seconds (1 hour)
DEFAULT_COMPRESS_AFTER_DAYS = 7
DEFAULT_LOG_DIR = "logs"

@dataclass
class LogConfig:
    """Configuration for logging system."""
    
    # Base paths
    log_dir: str = DEFAULT_LOG_DIR
    config_dir: str = "config"
    data_dir: str = "data"
    
    # Log file settings
    max_size_mb: int = DEFAULT_MAX_SIZE_MB
    max_files: int = DEFAULT_MAX_FILES
    compress_after_days: int = DEFAULT_COMPRESS_AFTER_DAYS
    
    # Batching settings
    batch_size: int = DEFAULT_BATCH_SIZE
    batch_timeout: int = DEFAULT_BATCH_TIMEOUT
    
    # Maintenance settings
    rotation_check_interval: int = DEFAULT_ROTATION_CHECK_INTERVAL
    cleanup_interval: int = DEFAULT_CLEANUP_INTERVAL
    
    # Logging settings
    level: LogLevel = LogLevel.INFO
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    
    # Optional settings
    log_to_console: bool = True
    log_to_file: bool = True
    log_file: Optional[str] = None
    
    def __post_init__(self):
        """Ensure required directories exist."""
        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        
        if self.log_file is None:
            self.log_file = os.path.join(self.log_dir, "social.log") 