import warnings
warnings.warn(
    "Deprecated: use dreamos.core.config.config_manager.ConfigManager instead.",
    DeprecationWarning,
)

"""
Log Configuration
---------------
This module is deprecated. Use dreamos.core.config.config_manager.ConfigManager instead.
"""

import logging
import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Set, Union
from dataclasses import dataclass, field
import json
import tempfile
from enum import Enum

from .log_types import RotationConfig
from .log_level import LogLevel

# Constants
DEFAULT_LOG_DIR = "logs"
DEFAULT_LOG_LEVEL = LogLevel.INFO
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
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 0.1

@dataclass
class LogConfig:
    """Configuration for logging system.
    
    Attributes:
        level: Logging level (string or LogLevel enum)
        log_dir: Directory for log files
        max_size_mb: Maximum size of log files in MB
        batch_size: Number of log entries to batch before writing
        output_format: Format for log output ("json", "text", or "markdown")
        platforms: Dictionary mapping platform names to log file names
        discord_webhook: Optional Discord webhook URL for logging
        discord_enabled: Whether Discord logging is enabled
        test_mode: Whether to run in test mode
        batch_timeout: Timeout for batch processing in seconds
        log_format: Format string for log messages
        date_format: Format string for timestamps
        max_age_days: Maximum age of log files in days
        max_files: Maximum number of backup files to keep
        compress_after_days: Number of days after which to compress old logs
        rotation_enabled: Whether log rotation is enabled
        max_retries: Maximum number of retries for failed operations
        retry_delay: Delay between retries in seconds
        use_temp_dir: Whether to use temporary directory for logs
        use_json: Whether to use JSON format for logs
        use_text: Whether to use text format for logs
        enable_discord: Whether to enable Discord logging
        discord_levels: List of log levels to send to Discord
        enable_metrics: Whether to enable metrics collection
        metrics_window: Time window for metrics in seconds
        rotation_check_interval: Interval for checking rotation in seconds
        cleanup_interval: Interval for cleanup in seconds
    """
    level: Union[str, LogLevel] = DEFAULT_LOG_LEVEL
    log_dir: str = field(default_factory=lambda: DEFAULT_LOG_DIR)
    max_size_mb: int = DEFAULT_MAX_SIZE_MB
    batch_size: int = DEFAULT_BATCH_SIZE
    output_format: str = "json"
    platforms: Dict[str, str] = field(default_factory=lambda: {
        "system": "system.log",
        "agent": "agent.log",
        "discord": "discord.log",
        "reddit": "reddit.log",
        "devlog": "devlog.log"
    })
    discord_webhook: Optional[str] = None
    discord_enabled: bool = False
    
    # Additional fields for backward compatibility
    test_mode: bool = False
    batch_timeout: float = DEFAULT_BATCH_TIMEOUT
    log_format: str = DEFAULT_LOG_FORMAT
    date_format: str = DEFAULT_DATE_FORMAT
    max_age_days: int = DEFAULT_MAX_AGE_DAYS
    max_files: int = DEFAULT_MAX_FILES
    compress_after_days: int = DEFAULT_COMPRESS_AFTER_DAYS
    rotation_enabled: bool = True
    max_retries: int = DEFAULT_MAX_RETRIES
    retry_delay: float = DEFAULT_RETRY_DELAY
    use_temp_dir: bool = False
    use_json: bool = True
    use_text: bool = True
    enable_discord: bool = False
    discord_levels: List[str] = field(default_factory=list)
    enable_metrics: bool = True
    metrics_window: int = DEFAULT_METRICS_WINDOW
    rotation_check_interval: float = DEFAULT_ROTATION_CHECK_INTERVAL
    cleanup_interval: float = DEFAULT_CLEANUP_INTERVAL
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        # Validate level
        if isinstance(self.level, str):
            try:
                self.level = LogLevel[self.level.upper()]
            except KeyError:
                raise ValueError(f"Invalid level: {self.level}. Must be one of: {[l.name for l in LogLevel]}")
                
        # Validate output format
        valid_formats = ["json", "text"]
        if self.output_format not in valid_formats:
            raise ValueError(f"Invalid format. Must be one of: {', '.join(valid_formats)}")
            
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
            
        # Handle log directory path
        if self.test_mode:
            self.use_temp_dir = True
            self.log_dir = os.path.join(tempfile.gettempdir(), "dream_os_logs")
        else:
            # Only convert to absolute path if not in test mode and not already absolute
            if not os.path.isabs(self.log_dir):
                self.log_dir = os.path.abspath(self.log_dir)
            # Create directory if it doesn't exist
            os.makedirs(self.log_dir, exist_ok=True)
        
        # Validate Discord settings
        if self.discord_enabled and not self.discord_webhook:
            raise ValueError("discord_webhook must be provided when discord_enabled is True")
        
    def get_rotation_config(self) -> RotationConfig:
        """Get rotation configuration.
        
        Returns:
            RotationConfig: Configuration for log rotation
        """
        return RotationConfig(
            max_size_mb=self.max_size_mb,
            max_files=self.max_files,
            max_age_days=self.max_age_days,
            compress_after_days=self.compress_after_days,
            backup_dir=os.path.join(self.log_dir, "backups")
        )
    
    @property
    def max_age(self) -> int:
        """Get max age in seconds."""
        return self.max_age_days * 24 * 60 * 60
    
    @property
    def backup_count(self) -> int:
        """Get number of backup files to keep."""
        return self.max_files
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "log_dir": self.log_dir,
            "level": self.level.name if isinstance(self.level, LogLevel) else str(self.level),
            "log_format": self.log_format,
            "date_format": self.date_format,
            "batch_size": self.batch_size,
            "batch_timeout": self.batch_timeout,
            "max_size_mb": self.max_size_mb,
            "max_files": self.max_files,
            "max_age_days": self.max_age_days,
            "compress_after_days": self.compress_after_days,
            "rotation_enabled": self.rotation_enabled,
            "platforms": self.platforms,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "test_mode": self.test_mode,
            "use_temp_dir": self.use_temp_dir,
            "use_json": self.use_json,
            "use_text": self.use_text,
            "enable_discord": self.enable_discord,
            "discord_webhook": self.discord_webhook,
            "discord_levels": self.discord_levels,
            "enable_metrics": self.enable_metrics,
            "metrics_window": self.metrics_window,
            "rotation_check_interval": self.rotation_check_interval,
            "cleanup_interval": self.cleanup_interval,
            "output_format": self.output_format
        }
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "LogConfig":
        """Create config from dictionary."""
        # Convert level to LogLevel if it's a string
        if "level" in config and isinstance(config["level"], str):
            config["level"] = LogLevel.from_str(config["level"])
        return cls(**config)
    
    def save(self, path: str) -> None:
        """Save config to file."""
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, path: str) -> "LogConfig":
        """Load config from file."""
        with open(path) as f:
            config = json.load(f)
        return cls.from_dict(config)
    
    def add_platform(self, platform: str, log_file: str) -> None:
        """Add a platform to the list."""
        self.platforms[platform] = log_file
    
    def remove_platform(self, platform: str) -> None:
        """Remove a platform from the list."""
        if platform in self.platforms:
            del self.platforms[platform]
    
    def copy(self) -> "LogConfig":
        """Create a copy of this config."""
        return LogConfig(**self.to_dict())
    
    def __str__(self) -> str:
        """String representation."""
        return (
            f"LogConfig(level={self.level}, "
            f"log_dir='{self.log_dir}', "
            f"max_size_mb={self.max_size_mb}, "
            f"batch_size={self.batch_size}, "
            f"output_format='{self.output_format}', "
            f"platforms={self.platforms}, "
            f"discord_webhook={self.discord_webhook}, "
            f"discord_enabled={self.discord_enabled})"
        )

    def __eq__(self, other: object) -> bool:
        """Compare two LogConfig instances."""
        if not isinstance(other, LogConfig):
            return False
        
        # Compare all fields
        return (
            self.level.value == other.level.value and  # Compare LogLevel values directly
            os.path.normcase(os.path.normpath(self.log_dir)) == os.path.normcase(os.path.normpath(other.log_dir)) and
            self.max_size_mb == other.max_size_mb and
            self.batch_size == other.batch_size and
            self.output_format == other.output_format and
            self.platforms == other.platforms and
            self.discord_webhook == other.discord_webhook and
            self.discord_enabled == other.discord_enabled and
            self.test_mode == other.test_mode and
            self.batch_timeout == other.batch_timeout and
            self.log_format == other.log_format and
            self.date_format == other.date_format and
            self.max_age_days == other.max_age_days and
            self.max_files == other.max_files and
            self.compress_after_days == other.compress_after_days and
            self.rotation_enabled == other.rotation_enabled and
            self.max_retries == other.max_retries and
            self.retry_delay == other.retry_delay and
            self.use_temp_dir == other.use_temp_dir and
            self.use_json == other.use_json and
            self.use_text == other.use_text and
            self.enable_discord == other.enable_discord and
            self.discord_levels == other.discord_levels and
            self.enable_metrics == other.enable_metrics and
            self.metrics_window == other.metrics_window and
            self.rotation_check_interval == other.rotation_check_interval and
            self.cleanup_interval == other.cleanup_interval
        )

    def update(self, updates: Dict[str, Any]) -> None:
        """Update configuration with new values.
        
        Args:
            updates: Dictionary of updates to apply
        """
        for key, value in updates.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # Re-validate after updates
        self.__post_init__()

    def __repr__(self) -> str:
        """Get string representation."""
        return (
            f"LogConfig(level={self.level}, "
            f"log_dir='{os.path.normpath(self.log_dir)}', "
            f"max_size_mb={self.max_size_mb}, "
            f"batch_size={self.batch_size}, "
            f"output_format='{self.output_format}', "
            f"platforms={self.platforms}, "
            f"discord_webhook={self.discord_webhook}, "
            f"discord_enabled={self.discord_enabled}, "
            f"test_mode={self.test_mode}, "
            f"batch_timeout={self.batch_timeout}, "
            f"log_format='{self.log_format}', "
            f"date_format='{self.date_format}', "
            f"max_age_days={self.max_age_days}, "
            f"max_files={self.max_files}, "
            f"compress_after_days={self.compress_after_days}, "
            f"rotation_enabled={self.rotation_enabled}, "
            f"max_retries={self.max_retries}, "
            f"retry_delay={self.retry_delay}, "
            f"use_temp_dir={self.use_temp_dir}, "
            f"use_json={self.use_json}, "
            f"use_text={self.use_text}, "
            f"enable_discord={self.enable_discord}, "
            f"discord_levels={self.discord_levels}, "
            f"enable_metrics={self.enable_metrics}, "
            f"metrics_window={self.metrics_window}, "
            f"rotation_check_interval={self.rotation_check_interval}, "
            f"cleanup_interval={self.cleanup_interval})"
        )

def setup_logging(
    level: Union[str, LogLevel] = DEFAULT_LOG_LEVEL,
    log_format: str = DEFAULT_LOG_FORMAT,
    date_format: str = DEFAULT_DATE_FORMAT
) -> None:
    """Set up basic logging configuration.
    
    Args:
        level: Log level (string or LogLevel enum)
        log_format: Log message format
        date_format: Date format for timestamps
    """
    # Convert level to LogLevel if it's a string
    if isinstance(level, str):
        level = LogLevel.from_str(level)
        
    # Configure logging
    logging.basicConfig(
        level=level.value,
        format=log_format,
        datefmt=date_format
    ) 