"""Logging configuration for the application."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
from pathlib import Path

class LogLevel(Enum):
    """Log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

@dataclass
class LogConfig:
    """Logging configuration."""
    
    level: LogLevel = LogLevel.INFO
    # how many days to keep rotated logs before the cleaner purges them
    max_age_days: int = 7
    log_dir: Path | str = Path("runtime/logs")
    _max_file_size: int = 10 * 1024 * 1024  # 10 MB
    max_files: int = 5
    batch_size: int = 1000
    batch_timeout: int = 5
    rotation_check_interval: int = 60
    compress_after_days: int = 7
    format: str = "%(asctime)s | %(levelname)s | %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    log_file: Optional[str] = None
    console_output: bool = True
    file_output: bool = True
    
    @property
    def max_file_size(self) -> int:
        """Get the maximum file size in bytes."""
        return self._max_file_size
    
    @max_file_size.setter
    def max_file_size(self, value: int) -> None:
        """Set the maximum file size in bytes."""
        self._max_file_size = value 