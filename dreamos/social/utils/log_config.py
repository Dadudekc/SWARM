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
    
    def __post_init__(self):
        """Initialize after dataclass creation."""
        # Convert string path to Path if needed
        if isinstance(self.log_dir, str):
            self.log_dir = Path(self.log_dir)
            
        # Create log directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize platform log files
        self._init_platform_logs()
    
    def _init_platform_logs(self):
        """Initialize log files for each platform."""
        default_platforms = ["default", "system", "error"]
        for platform in default_platforms:
            log_file = self.log_dir / f"{platform}.log"
            self.platforms[platform] = log_file
            log_file.touch(exist_ok=True)
    
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
