"""
Log configuration module for managing log files and settings.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
from .log_level import LogLevel

@dataclass
class LogConfig:
    """Configuration for log files and settings."""
    
    log_dir: str = "logs"
    max_size_mb: int = 10
    max_files: int = 5
    compress_after_days: int = 7
    level: LogLevel = LogLevel.INFO
    platforms: List[str] = field(default_factory=lambda: ["twitter", "facebook", "instagram", "linkedin"])
    data_dir: str = "runtime/logs/data"
    config_dir: str = "runtime/logs/config"
    log_file: Optional[Path] = None
    batch_size: int = 100  # Default batch size for log entries
    batch_timeout: float = 5.0  # Default batch timeout in seconds
    format: str = "%(asctime)s [%(levelname)-8s] %(message)s"  # Default log format
    
    def __post_init__(self):
        """Initialize paths and create directories."""
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
            
        # Create default log files for each platform
        for platform in self.platforms:
            platform_log = self.log_dir / f"{platform}.log"
            if not platform_log.exists():
                platform_log.touch()
                
        # Create main social log if it doesn't exist
        if not self.log_file.exists():
            self.log_file.touch()
    
    @property
    def max_bytes(self) -> int:
        """Get maximum file size in bytes."""
        return self.max_size_mb * 1024 * 1024
    
    @property
    def file_path(self) -> Path:
        """Get the main log file path (for backward compatibility)."""
        return self.log_file
    
    def __eq__(self, other):
        """Compare two LogConfig instances."""
        if not isinstance(other, LogConfig):
            return False
        return (
            self.log_dir == other.log_dir and
            self.max_size_mb == other.max_size_mb and
            self.max_files == other.max_files and
            self.compress_after_days == other.compress_after_days and
            self.level == other.level and
            self.platforms == other.platforms and
            self.batch_size == other.batch_size and
            self.batch_timeout == other.batch_timeout and
            self.format == other.format
        )
