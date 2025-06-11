"""
Log Rotator Module
-----------------
Handles log file rotation and cleanup to manage disk space.
"""

import os
import time
import logging
import shutil
import json
import gzip
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta

from .log_types import RotationConfig
from .log_config import LogConfig

__all__ = [
    'LogRotator',
    '_get_file_size',
    '_get_file_age',
    '_rotate_file',
    '_cleanup_old_backups',
    'check_rotation',
    'rotate_all',
    'get_rotation_info',
    'rotate'
]

logger = logging.getLogger(__name__)

class LogRotator:
    """Handles log file rotation and compression."""
    
    def __init__(self, log_dir: Union[str, Path, LogConfig], max_size_mb: int = 10,
                 max_files: int = 5, compress_after_days: int = 7):
        """Initialize the log rotator.
        
        Args:
            log_dir: Log directory path or LogConfig object
            max_size_mb: Maximum file size in MB
            max_files: Maximum number of backup files
            compress_after_days: Days after which to compress old logs
        """
        if isinstance(log_dir, LogConfig):
            self.log_dir = Path(log_dir.log_dir)
            self.max_size_mb = log_dir.max_size_mb
            self.max_files = log_dir.max_files
            self.compress_after_days = log_dir.compress_after_days
        else:
            self.log_dir = Path(log_dir)
            self.max_size_mb = max_size_mb
            self.max_files = max_files
            self.compress_after_days = compress_after_days
            
        # Create log directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def max_bytes(self) -> int:
        """Get maximum file size in bytes."""
        return self.max_size_mb * 1024 * 1024
    
    def check_rotation(self, file_path: Union[str, Path]) -> bool:
        """Check if a log file needs rotation.
        
        Args:
            file_path: Path to log file
            
        Returns:
            True if file needs rotation, False otherwise
        """
        file_path = Path(file_path)
        if not file_path.exists():
            return False
            
        # Check file size
        if file_path.stat().st_size >= self.max_bytes:
            return True
            
        # Check file age
        file_age = datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)
        if file_age.days >= self.compress_after_days:
            return True
            
        return False
    
    def _rotate_file(self, file_path: Union[str, Path]) -> bool:
        """Rotate a log file.
        
        Args:
            file_path: Path to log file
            
        Returns:
            True if rotation was successful, False otherwise
        """
        file_path = Path(file_path)
        if not file_path.exists():
            return False
            
        try:
            # Generate rotated file name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            rotated_path = file_path.parent / f"{file_path.stem}_{timestamp}{file_path.suffix}"
            
            # Move current file to backup
            shutil.move(str(file_path), str(rotated_path))
            
            # Create new empty file
            file_path.touch()
            
            # Clean up old backups
            self._cleanup_old_backups(file_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Error rotating file {file_path}: {e}")
            return False
    
    def rotate_all(self) -> List[Path]:
        """Rotate all log files in the directory.
        
        Returns:
            List of rotated file paths
        """
        rotated_files = []
        for file_path in self.log_dir.glob("*.log"):
            if self.check_rotation(file_path):
                if self._rotate_file(file_path):
                    rotated_files.append(file_path)
        return rotated_files
    
    def _cleanup_old_backups(self, file_path: Union[str, Path]) -> None:
        """Clean up old backup files.
        
        Args:
            file_path: Path to log file
        """
        file_path = Path(file_path)
        pattern = f"{file_path.stem}_*{file_path.suffix}"
        
        # Get all backup files
        backups = sorted(
            self.log_dir.glob(pattern),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        # Remove excess backups
        for backup in backups[self.max_files:]:
            try:
                backup.unlink()
            except Exception as e:
                logger.error(f"Error removing backup {backup}: {e}")
    
    def get_rotation_info(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Get rotation information for a file.
        
        Args:
            file_path: Path to log file
            
        Returns:
            Dictionary with rotation information
        """
        file_path = Path(file_path)
        if not file_path.exists():
            return {
                "needs_rotation": False,
                "size": 0,
                "age_days": 0,
                "backup_count": 0
            }
            
        size = file_path.stat().st_size
        age = datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)
        
        # Count backup files
        pattern = f"{file_path.stem}_*{file_path.suffix}"
        backup_count = len(list(self.log_dir.glob(pattern)))
        
        return {
            "needs_rotation": self.check_rotation(file_path),
            "size": size,
            "age_days": age.days,
            "backup_count": backup_count
        }

    def _get_file_size(self, file_path: Union[str, Path]) -> int:
        """Get file size in bytes.
        
        Args:
            file_path: Path to file
            
        Returns:
            File size in bytes
        """
        try:
            return os.path.getsize(file_path)
        except OSError as e:
            logger.error(f"Error getting file size for {file_path}: {e}")
            return 0
    
    def _get_file_age(self, file_path: Union[str, Path]) -> float:
        """Get file age in days.
        
        Args:
            file_path: Path to file
            
        Returns:
            File age in days
        """
        try:
            mtime = os.path.getmtime(file_path)
            age = time.time() - mtime
            return age / (24 * 3600)  # Convert to days
        except OSError as e:
            logger.error(f"Error getting file age for {file_path}: {e}")
            return 0.0

    def rotate(self, filepath: str) -> str:
        """Rotate a log file by path and return the new backup path."""
        path = Path(filepath)
        if not path.exists():
            return ""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            backup_path = path.with_name(f"{path.stem}_{timestamp}{path.suffix}")
            shutil.move(str(path), str(backup_path))
            path.touch()
            logger.info(f"Rotated log file {path} to {backup_path}")
            return str(backup_path)
        except Exception as e:
            logger.error(f"Error rotating file {path}: {e}")
            return "" 
