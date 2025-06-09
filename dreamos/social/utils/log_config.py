"""
Log configuration module.
"""

from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass, field
from .log_level import LogLevel

@dataclass
class LogConfig:
    """Configuration for logging system."""
    
    log_dir: Path
    max_size_mb: int = 10
    max_files: int = 5
    batch_size: int = 100
    batch_timeout: float = 5.0
    level: LogLevel = LogLevel.INFO
    platforms: Dict[str, Path] = field(default_factory=dict)
    compress_after_days: int = 7
    format: str = "%(asctime)s [%(levelname)-8s] %(message)s (%(filename)s:%(lineno)d)"
    config_dir: Optional[Path] = None
    
    def __post_init__(self):
        """Initialize configuration after construction."""
        # Convert string paths to Path objects
        if isinstance(self.log_dir, str):
            self.log_dir = Path(self.log_dir)
        if isinstance(self.config_dir, str):
            self.config_dir = Path(self.config_dir)
            
        # Set config_dir to log_dir if not specified
        if self.config_dir is None:
            self.config_dir = self.log_dir
            
        # Create directories
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize platform logs
        self._init_platform_logs()
    
    def _init_platform_logs(self):
        """Initialize default platform log files."""
        default_platforms = {
            'default': 'default.log',
            'system': 'system.log',
            'error': 'error.log'
        }
        
        for platform, filename in default_platforms.items():
            log_path = self.log_dir / filename
            self.platforms[platform] = log_path
            
            # Ensure log file exists
            log_path.parent.mkdir(parents=True, exist_ok=True)
            if not log_path.exists():
                log_path.touch()
    
    @property
    def log_file(self) -> Path:
        """Get the default log file path."""
        return self.log_dir / 'log.txt'
    
    @property
    def data_dir(self) -> Path:
        """Get the data directory path."""
        return self.log_dir / 'data'
    
    def __str__(self) -> str:
        """String representation of the configuration."""
        return f"LogConfig(log_dir={self.log_dir}, level={self.level})"
    
    def __eq__(self, other) -> bool:
        """Compare configurations for equality."""
        if not isinstance(other, LogConfig):
            return False
        return str(self.log_dir) == str(other.log_dir)
    
    @property
    def max_bytes(self) -> int:
        """Get maximum log file size in bytes."""
        return self.max_size_mb * 1024 * 1024
    
    def add_platform(self, platform: str) -> Path:
        """Add a new platform log file.
        
        Args:
            platform: Platform name
            
        Returns:
            Path to platform log file
        """
        if platform not in self.platforms:
            log_file = self.log_dir / f"{platform}.log"
            self.platforms[platform] = log_file
            log_file.touch(exist_ok=True)
        return self.platforms[platform]
    
    def get_platform_log(self, platform: str) -> Optional[Path]:
        """Get log file path for a platform.
        
        Args:
            platform: Platform name
            
        Returns:
            Path to platform log file or None if not found
        """
        return self.platforms.get(platform)
