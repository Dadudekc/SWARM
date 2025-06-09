"""
Log Rotator Module
-----------------
Handles log file rotation and cleanup to manage disk space.
"""

import os
import time
import logging
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta

from .log_types import RotationConfig

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
    """Handles log file rotation and cleanup."""
    
    def __init__(self, log_dir: Path, max_size_mb: int = 10, max_files: int = 5, 
                 compress_after_days: int = 7):
        """Initialize the log rotator.
        
        Args:
            log_dir: Directory containing log files
            max_size_mb: Maximum size of log files in MB
            max_files: Maximum number of backup files to keep
            compress_after_days: Days after which to compress old backups
        """
        self.log_dir = Path(log_dir)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_files = max_files
        self.compress_after_days = compress_after_days
        self.logger = logging.getLogger(__name__)
    
    def _get_file_size(self, file_path: Path) -> int:
        """Get file size in bytes.
        
        Args:
            file_path: Path to file
            
        Returns:
            File size in bytes
        """
        try:
            return file_path.stat().st_size
        except Exception as e:
            self.logger.error(f"Error getting file size for {file_path}: {e}")
            return 0
    
    def _get_file_age(self, file_path: Path) -> float:
        """Get file age in days.
        
        Args:
            file_path: Path to file
            
        Returns:
            File age in days
        """
        try:
            mtime = file_path.stat().st_mtime
            age_seconds = time.time() - mtime
            return age_seconds / (24 * 3600)  # Convert to days
        except Exception as e:
            self.logger.error(f"Error getting file age for {file_path}: {e}")
            return 0
    
    def _rotate_file(self, file_path: Path) -> bool:
        """Rotate a single log file.
        
        Args:
            file_path: Path to log file
            
        Returns:
            True if rotation was successful
        """
        try:
            if not file_path.exists():
                return False
                
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            backup_path = file_path.parent / f"{file_path.stem}_{timestamp}{file_path.suffix}"
            
            # Rename current file to backup
            file_path.rename(backup_path)
            
            # Create new empty file
            file_path.touch()
            file_path.write_text("")  # Ensure file is empty
            
            self.logger.info(f"Rotated log file {file_path} to {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error rotating file {file_path}: {e}")
            return False
    
    def _cleanup_old_backups(self, file_path: Path) -> None:
        """Clean up old backup files.
        
        Args:
            file_path: Path to log file
        """
        try:
            # Get all backup files for this log file
            backup_files = list(file_path.parent.glob(f"{file_path.stem}_*{file_path.suffix}"))
            
            # Sort by modification time (oldest first)
            backup_files.sort(key=lambda x: x.stat().st_mtime)
            
            # Keep only the most recent files
            while len(backup_files) > self.max_files:
                old_file = backup_files.pop(0)
                try:
                    old_file.unlink()
                    self.logger.info(f"Removed old backup file: {old_file}")
                except Exception as e:
                    self.logger.error(f"Error removing old backup file {old_file}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error cleaning up old backups: {e}")
    
    def _compress_old_backups(self, file_path: Path) -> None:
        """Compress old backup files.
        
        Args:
            file_path: Path to log file
        """
        try:
            # Get all backup files for this log file
            backup_files = list(file_path.parent.glob(f"{file_path.stem}_*{file_path.suffix}"))
            
            for backup_file in backup_files:
                # Check if file is old enough to compress
                if self._get_file_age(backup_file) >= self.compress_after_days:
                    # Skip if already compressed
                    if backup_file.suffix == '.gz':
                        continue
                        
                    # Compress file
                    try:
                        with open(backup_file, 'rb') as f_in:
                            with open(backup_file.with_suffix('.gz'), 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        backup_file.unlink()  # Remove original file
                        self.logger.info(f"Compressed old backup file: {backup_file}")
                    except Exception as e:
                        self.logger.error(f"Error compressing backup file {backup_file}: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error compressing old backups: {e}")
    
    def check_rotation(self, file_path: Path) -> bool:
        """Check if a file needs rotation.
        
        Args:
            file_path: Path to log file
            
        Returns:
            True if file needs rotation
        """
        try:
            if not file_path.exists():
                return False
                
            # Check file size
            if self._get_file_size(file_path) >= self.max_size_bytes:
                return True
                
            # Check file age
            if self._get_file_age(file_path) >= self.compress_after_days:
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking rotation for {file_path}: {e}")
            return False
    
    def rotate_all(self) -> None:
        """Rotate all log files in the directory."""
        try:
            # Get all log files
            log_files = list(self.log_dir.glob("*.log"))
            
            for log_file in log_files:
                if self.check_rotation(log_file):
                    if self._rotate_file(log_file):
                        self._cleanup_old_backups(log_file)
                        self._compress_old_backups(log_file)
                        
        except Exception as e:
            self.logger.error(f"Error rotating all log files: {e}")
    
    def get_rotation_info(self, file_path: Path) -> dict:
        """Get information about file rotation status.
        
        Args:
            file_path: Path to log file
            
        Returns:
            Dictionary containing rotation information
        """
        try:
            info = {
                "size_bytes": self._get_file_size(file_path),
                "age_days": self._get_file_age(file_path),
                "needs_rotation": self.check_rotation(file_path),
                "backup_count": len(list(file_path.parent.glob(f"{file_path.stem}_*{file_path.suffix}")))
            }
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting rotation info for {file_path}: {e}")
            return {
                "size_bytes": 0,
                "age_days": 0,
                "needs_rotation": False,
                "backup_count": 0
            }
    
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
