"""
Log Rotator Module
-----------------
Provides functionality for rotating log files based on size and time.
"""

from typing import Optional
from pathlib import Path
from datetime import datetime
import shutil
import os

class RotationConfig:
    """Configuration for log rotation."""
    def __init__(
        self,
        max_size_mb: int = 10,
        max_files: int = 5,
        rotation_interval_days: int = 7
    ):
        self.max_size_mb = max_size_mb
        self.max_files = max_files
        self.rotation_interval_days = rotation_interval_days

class LogRotator:
    """Handles rotation of log files."""
    
    def __init__(
        self,
        log_dir: str,
        config: Optional[RotationConfig] = None
    ):
        """Initialize the log rotator.
        
        Args:
            log_dir: Directory containing log files
            config: Optional rotation configuration
        """
        self.log_dir = Path(log_dir)
        self.config = config or RotationConfig()
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def should_rotate(self, log_file: str) -> bool:
        """Check if a log file should be rotated.
        
        Args:
            log_file: Path to the log file
            
        Returns:
            True if the file should be rotated, False otherwise
        """
        file_path = self.log_dir / log_file
        
        if not file_path.exists():
            return False
            
        # Check file size
        size_mb = file_path.stat().st_size / (1024 * 1024)
        if size_mb >= self.config.max_size_mb:
            return True
            
        # Check file age
        file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
        age_days = (datetime.now() - file_time).days
        if age_days >= self.config.rotation_interval_days:
            return True
            
        return False
    
    def rotate(self, log_file: str) -> None:
        """Rotate a log file.
        
        Args:
            log_file: Name of the log file to rotate
        """
        file_path = self.log_dir / log_file
        
        # Remove oldest file if we've hit the limit
        oldest_file = self.log_dir / f"{log_file}.{self.config.max_files}"
        if oldest_file.exists():
            oldest_file.unlink()
        
        # Rotate existing files
        for i in range(self.config.max_files - 1, 0, -1):
            old_file = self.log_dir / f"{log_file}.{i}"
            new_file = self.log_dir / f"{log_file}.{i + 1}"
            if old_file.exists():
                shutil.move(old_file, new_file)
        
        # Move current file to .1
        if file_path.exists():
            shutil.move(file_path, self.log_dir / f"{log_file}.1")
        
        # Create new empty file
        file_path.touch() 