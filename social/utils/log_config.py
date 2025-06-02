"""
Log Config Module
----------------
Provides configuration for logging setup.
"""

import logging
import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Set
from enum import Enum
from dataclasses import dataclass, field
import json
import tempfile

# Constants
DEFAULT_LOG_DIR = "logs"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
DEFAULT_BATCH_SIZE = 100
DEFAULT_BATCH_TIMEOUT = 60.0
DEFAULT_ROTATION_SIZE = 1024 * 1024  # 1MB
DEFAULT_MAX_FILES = 5
DEFAULT_ROTATION_CHECK_INTERVAL = 300.0
DEFAULT_CLEANUP_INTERVAL = 3600.0
DEFAULT_METRICS_WINDOW = 3600
DEFAULT_MAX_AGE_DAYS = 30
DEFAULT_MAX_SIZE_MB = 10
DEFAULT_COMPRESS_AFTER_DAYS = 1

class LogLevel(Enum):
    """Logging levels as an enum for type safety."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
    
    @classmethod
    def from_str(cls, level: str) -> 'LogLevel':
        """Convert string to LogLevel.
        
        Args:
            level: Log level string
            
        Returns:
            LogLevel enum value
            
        Raises:
            ValueError: If level is invalid
        """
        try:
            return cls[level.upper()]
        except KeyError:
            raise ValueError(f"Invalid log level: {level}. Must be one of: {[l.name for l in cls]}")

@dataclass
class LogConfig:
    """Configuration for logging setup."""
    log_dir: str = DEFAULT_LOG_DIR
    level: str = DEFAULT_LOG_LEVEL
    format: str = DEFAULT_LOG_FORMAT
    date_format: str = DEFAULT_DATE_FORMAT
    batch_size: int = DEFAULT_BATCH_SIZE
    batch_timeout: float = DEFAULT_BATCH_TIMEOUT
    rotation_size: int = DEFAULT_ROTATION_SIZE
    max_files: int = DEFAULT_MAX_FILES
    rotation_check_interval: float = DEFAULT_ROTATION_CHECK_INTERVAL
    cleanup_interval: float = DEFAULT_CLEANUP_INTERVAL
    use_temp_dir: bool = False
    use_json: bool = True
    use_text: bool = True
    enable_discord: bool = False
    discord_webhook_url: Optional[str] = None
    discord_levels: List[str] = field(default_factory=list)
    enable_metrics: bool = True
    metrics_window: int = DEFAULT_METRICS_WINDOW
    max_age_days: int = DEFAULT_MAX_AGE_DAYS
    max_size_mb: int = DEFAULT_MAX_SIZE_MB
    compress_after_days: int = DEFAULT_COMPRESS_AFTER_DAYS
    platforms: Dict[str, str] = field(default_factory=dict)
    max_retries: int = 3
    retry_delay: float = 0.1
    test_mode: bool = False
    
    def __post_init__(self):
        """Validate and normalize configuration after initialization."""
        # Validate log level
        self.level = LogLevel.from_str(self.level)
        
        # Normalize log directory
        if self.use_temp_dir:
            self.log_dir = str(Path(tempfile.gettempdir()) / "dream_os_logs")
        else:
            self.log_dir = str(Path(self.log_dir).resolve())
        
        # Validate numeric values
        if self.batch_size < 1:
            raise ValueError("batch_size must be positive")
        if self.batch_timeout < 0:
            raise ValueError("batch_timeout must be non-negative")
        if self.rotation_size < 1024:  # At least 1KB
            raise ValueError("rotation_size must be at least 1KB")
        if self.max_files < 1:
            raise ValueError("max_files must be positive")
        if self.rotation_check_interval < 1:
            raise ValueError("rotation_check_interval must be at least 1 second")
        if self.cleanup_interval < 1:
            raise ValueError("cleanup_interval must be at least 1 second")
        if self.metrics_window < 1:
            raise ValueError("metrics_window must be positive")
        if self.max_age_days < 1:
            raise ValueError("max_age_days must be positive")
        if self.max_size_mb < 1:
            raise ValueError("max_size_mb must be positive")
        if self.compress_after_days < 0:
            raise ValueError("compress_after_days must be non-negative")
        
        # Validate Discord configuration
        if self.enable_discord and not self.discord_webhook_url:
            raise ValueError("discord_webhook_url is required when enable_discord is True")
        if self.discord_levels:
            valid_levels = {level.name for level in LogLevel}
            invalid_levels = set(self.discord_levels) - valid_levels
            if invalid_levels:
                raise ValueError(f"Invalid Discord log levels: {invalid_levels}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.
        
        Returns:
            Dict containing configuration
        """
        return {
            "log_dir": self.log_dir,
            "level": self.level.name,
            "format": self.format,
            "date_format": self.date_format,
            "batch_size": self.batch_size,
            "batch_timeout": self.batch_timeout,
            "rotation_size": self.rotation_size,
            "max_files": self.max_files,
            "rotation_check_interval": self.rotation_check_interval,
            "cleanup_interval": self.cleanup_interval,
            "use_temp_dir": self.use_temp_dir,
            "use_json": self.use_json,
            "use_text": self.use_text,
            "enable_discord": self.enable_discord,
            "discord_webhook_url": self.discord_webhook_url,
            "discord_levels": self.discord_levels,
            "enable_metrics": self.enable_metrics,
            "metrics_window": self.metrics_window,
            "max_age_days": self.max_age_days,
            "max_size_mb": self.max_size_mb,
            "compress_after_days": self.compress_after_days,
            "platforms": self.platforms,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "test_mode": self.test_mode
        }
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'LogConfig':
        """Create configuration from dictionary.
        
        Args:
            config: Dictionary containing configuration
            
        Returns:
            LogConfig instance
        """
        return cls(**config)
    
    def save(self, file_path: str) -> None:
        """Save configuration to file.
        
        Args:
            file_path: Path to save configuration
        """
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, file_path: str) -> 'LogConfig':
        """Load configuration from file.
        
        Args:
            file_path: Path to load configuration from
            
        Returns:
            LogConfig instance
        """
        with open(file_path) as f:
            return cls.from_dict(json.load(f))
    
    def add_platform(self, platform: str, log_file: str) -> None:
        """Add a platform and its log file.
        
        Args:
            platform: Platform name
            log_file: Log file path
        """
        self.platforms[platform] = str(Path(log_file).resolve())

def setup_logging(
    log_dir: Optional[str] = None,
    level: str = DEFAULT_LOG_LEVEL,
    format: str = DEFAULT_LOG_FORMAT,
    date_format: str = DEFAULT_DATE_FORMAT
) -> None:
    """Configure logging for the application.
    
    Args:
        log_dir: Directory to store log files. If None, logs to console only
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Log message format
        date_format: Date format for log messages
    """
    try:
        # Create root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(LogLevel.from_str(level).value)
        
        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Create formatter
        formatter = logging.Formatter(format, date_format)
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # Add file handler if log_dir is provided
        if log_dir:
            log_path = Path(log_dir)
            log_path.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path / "app.log")
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
    except Exception as e:
        print(f"Error setting up logging: {str(e)}")
        raise 