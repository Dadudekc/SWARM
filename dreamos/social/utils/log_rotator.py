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
    
    def __init__(self, log_dir: Path, max_size_mb: int = 10, max_files: int = 5, compress_after_days: int = 7):
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
        
        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
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
            logger.error(f"Error getting file size for {file_path}: {e}")
            return 0
    
    def _get_file_age(self, file_path: Path) -> int:
        """Get file age in days.
        
        Args:
            file_path: Path to file
            
        Returns:
            File age in days
        """
        try:
            mtime = file_path.stat().st_mtime
            age = datetime.now() - datetime.fromtimestamp(mtime)
            return age.days
        except Exception as e:
            logger.error(f"Error getting file age for {file_path}: {e}")
            return 0
    
    def _rotate_file(self, file_path: Path) -> bool:
        """Rotate a log file.
        
        Args:
            file_path: Path to log file
            
        Returns:
            True if rotation was successful
        """
        if not file_path.exists():
            return False
            
        try:
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = file_path.parent / f"{file_path.stem}_{timestamp}{file_path.suffix}"
            
            # Move current file to backup
            shutil.move(str(file_path), str(backup_path))
            
            # Create new empty file
            file_path.touch()
            
            # Clean up old backups
            self._cleanup_old_backups(file_path)
            
            return True
        except Exception as e:
            logger.error(f"Error rotating file {file_path}: {e}")
            return False
    
    def _cleanup_old_backups(self, file_path: Path) -> None:
        """Clean up old backup files.
        
        Args:
            file_path: Path to current log file
        """
        try:
            # Get all backup files
            backup_pattern = f"{file_path.stem}_*{file_path.suffix}"
            backup_files = sorted(
                file_path.parent.glob(backup_pattern),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            
            # Remove excess backups
            for backup_file in backup_files[self.max_files:]:
                try:
                    backup_file.unlink()
                except Exception as e:
                    logger.error(f"Error deleting backup {backup_file}: {e}")
                    
            # Compress old backups
            self._compress_old_backups(file_path)
        except Exception as e:
            logger.error(f"Error cleaning up backups for {file_path}: {e}")
    
    def _compress_old_backups(self, file_path: Path) -> None:
        """Compress old backup files.
        
        Args:
            file_path: Path to current log file
        """
        try:
            # Get all backup files
            backup_pattern = f"{file_path.stem}_*{file_path.suffix}"
            backup_files = file_path.parent.glob(backup_pattern)
            
            for backup_file in backup_files:
                # Skip already compressed files
                if backup_file.suffix == '.gz':
                    continue
                    
                # Check file age
                if self._get_file_age(backup_file) >= self.compress_after_days:
                    try:
                        # Compress file
                        with open(backup_file, 'rb') as f_in:
                            with gzip.open(f"{backup_file}.gz", 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        
                        # Remove original
                        backup_file.unlink()
                    except Exception as e:
                        logger.error(f"Error compressing {backup_file}: {e}")
        except Exception as e:
            logger.error(f"Error compressing backups for {file_path}: {e}")
    
    def check_rotation(self, file_path: Path) -> bool:
        """Check if a file needs rotation.
        
        Args:
            file_path: Path to log file
            
        Returns:
            True if file should be rotated
        """
        if not file_path.exists():
            return False
            
        try:
            # Check file size
            if self._get_file_size(file_path) >= self.max_size_bytes:
                return True
                
            # Check file age
            if self._get_file_age(file_path) >= self.compress_after_days:
                return True
                
            return False
        except Exception as e:
            logger.error(f"Error checking rotation for {file_path}: {e}")
            return False
    
    def rotate_all(self) -> None:
        """Rotate all log files in the directory."""
        try:
            for file_path in self.log_dir.glob("*.log"):
                if self.check_rotation(file_path):
                    self._rotate_file(file_path)
        except Exception as e:
            logger.error(f"Error rotating all files: {e}")
    
    def get_rotation_info(self, file_path: Path) -> Dict[str, Any]:
        """Get information about file rotation status.
        
        Args:
            file_path: Path to log file
            
        Returns:
            Dictionary containing rotation information
        """
        info = {
            "size": self._get_file_size(file_path),
            "age_days": self._get_file_age(file_path),
            "needs_rotation": False,
            "backup_count": 0
        }
        
        try:
            # Check if rotation needed
            info["needs_rotation"] = self.check_rotation(file_path)
            
            # Count backup files
            backup_pattern = f"{file_path.stem}_*{file_path.suffix}"
            info["backup_count"] = len(list(file_path.parent.glob(backup_pattern)))
        except Exception as e:
            logger.error(f"Error getting rotation info for {file_path}: {e}")
            
        return info
    
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
