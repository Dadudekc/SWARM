"""
Log configuration for managing log files and settings.
"""

import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Union

from .log_level import LogLevel

@dataclass
class LogConfig:
    """Configuration for log files and settings."""
    log_dir: Union[str, Path]
    max_size_mb: int = 10
    max_files: int = 5
    backup_count: int = 5  # Alias for max_files for backward compatibility
    compress_after_days: int = 7
    data_dir: Union[str, Path] = Path("runtime/logs/data")
    batch_size: int = 100
    batch_timeout: float = 5.0
    level: LogLevel = LogLevel.INFO
    platforms: Dict[str, Path] = field(default_factory=dict)
    format: str = "%(asctime)s [%(levelname)-8s] %(message)s"
    config_dir: Union[str, Path] = Path("runtime/logs/config")
    log_file: Optional[Union[str, Path]] = None

    def __post_init__(self):
        """Initialize paths and create necessary directories."""
        # Convert string paths to Path objects
        self.log_dir = Path(self.log_dir)
        self.data_dir = Path(self.data_dir)
        self.config_dir = Path(self.config_dir)
        
        # Create directories if they don't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Set default log file if not specified
        if self.log_file is None:
            self.log_file = self.log_dir / "social.log"
        else:
            self.log_file = Path(self.log_file)
            
        # Set platform log files if not specified
        if not self.platforms:
            self.platforms = {
                "twitter": self.log_dir / "twitter.log",
                "facebook": self.log_dir / "facebook.log",
                "instagram": self.log_dir / "instagram.log",
                "linkedin": self.log_dir / "linkedin.log"
            }
        else:
            self.platforms = {k: Path(v) for k, v in self.platforms.items()}

    @property
    def max_bytes(self) -> int:
        """Get maximum file size in bytes."""
        return self.max_size_mb * 1024 * 1024

    @property
    def file_path(self) -> Path:
        """Legacy property for backward compatibility."""
        return self.log_file

    def __str__(self) -> str:
        """Get string representation."""
        return str(self.log_dir)
    
    def __eq__(self, other):
        """Compare two LogConfig instances."""
        if not isinstance(other, LogConfig):
            return False
        return (
            self.log_dir == other.log_dir
            and self.max_size_mb == other.max_size_mb
            and self.max_files == other.max_files
            and self.compress_after_days == other.compress_after_days
            and self.data_dir == other.data_dir
            and self.batch_size == other.batch_size
            and self.batch_timeout == other.batch_timeout
            and self.level == other.level
            and self.platforms == other.platforms
            and self.format == other.format
            and self.config_dir == other.config_dir
            and self.log_file == other.log_file
        )
