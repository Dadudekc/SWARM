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
    
    def __init__(
        self,
        log_dir: Union[str, Path, LogConfig],
        max_size_mb: int = 10,
        max_files: int = 5,
        backup_count: Optional[int] = None,  # Alias for max_files
        compress_after_days: int = 7,
        max_age_days: Optional[int] = None  # Alias for compress_after_days
    ):
        """Initialize log rotator.
        
        Args:
            log_dir: Log directory path or LogConfig object
            max_size_mb: Maximum file size in MB
            max_files: Maximum number of backup files
            backup_count: Alias for max_files (legacy support)
            compress_after_days: Days before compression
            max_age_days: Alias for compress_after_days (legacy support)
        """
        if isinstance(log_dir, LogConfig):
            self._config = log_dir
            self.log_dir = log_dir.log_dir
            self.max_size_mb = log_dir.max_size_mb
            self.max_files = log_dir.max_files
            self.compress_after_days = log_dir.compress_after_days
        else:
            self._config = None
            self.log_dir = Path(log_dir)
            self.max_size_mb = max_size_mb
            self.max_files = backup_count if backup_count is not None else max_files
            self.compress_after_days = max_age_days if max_age_days is not None else compress_after_days
            
        if backup_count is not None:
            logging.warning("backup_count parameter is deprecated, use max_files instead")
        if max_age_days is not None:
            logging.warning("max_age_days parameter is deprecated, use compress_after_days instead")

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
            return 0
    
    def _rotate_file(self, file_path: Union[str, Path]) -> bool:
        """Rotate a log file.
        
        Args:
            file_path: Path to log file
            
        Returns:
            True if rotation was successful
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return False
            
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = file_path.parent / f"{file_path.stem}_{timestamp}{file_path.suffix}"
            
            # Move current file to backup
            shutil.move(str(file_path), str(backup_path))
            
            # Create new empty log file
            file_path.touch()
            
            logger.info(f"Rotated log file {file_path} to {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error rotating file {file_path}: {e}")
            return False
    
    def _cleanup_old_backups(self, file_path: Union[str, Path]) -> None:
        """Clean up old backup files.
        
        Args:
            file_path: Base file path
        """
        try:
            file_path = Path(file_path)
            pattern = f"{file_path.stem}.*.log"
            
            # Get all backup files
            backups = sorted(
                self.log_dir.glob(pattern),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            
            # Remove excess backups
            for backup in backups[self.max_files:]:
                try:
                    backup.unlink()
                    logger.info(f"Removed old backup {backup}")
                except Exception as e:
                    logger.error(f"Error removing backup {backup}: {e}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up backups for {file_path}: {e}")
    
    def _compress_backup(self, backup_path: Union[str, Path]) -> None:
        """Compress a backup file.
        
        Args:
            backup_path: Path to backup file
        """
        try:
            backup_path = Path(backup_path)
            if not backup_path.exists():
                return
            
            # Check if already compressed
            if backup_path.suffix == ".gz":
                return
            
            # Compress file
            with open(backup_path, "rb") as f_in:
                with gzip.open(f"{backup_path}.gz", "wb") as f_out:
                    f_out.writelines(f_in)
            
            # Remove original
            backup_path.unlink()
            logger.info(f"Compressed backup {backup_path}")
            
        except Exception as e:
            logger.error(f"Error compressing backup {backup_path}: {e}")
    
    def check_rotation(self, log_file: Union[str, Path]) -> bool:
        """Check if file needs rotation.
        
        Args:
            log_file: Path to log file
            
        Returns:
            True if rotation needed
        """
        log_file = Path(log_file)
        if not log_file.exists():
            return False
            
        # Check file size
        if log_file.stat().st_size >= self.max_size_mb * 1024 * 1024:
            return True
            
        # Check file age
        if self._get_file_age(log_file) >= self.compress_after_days:
            return True
            
        return False

    def rotate_file(self, log_file: Union[str, Path]) -> bool:
        """Rotate a log file.
        
        Args:
            log_file: Path to log file
            
        Returns:
            True if successful
        """
        log_file = Path(log_file)
        if not log_file.exists():
            return False
            
        try:
            # Create backup filename
            backup_file = log_file.with_suffix(f"{log_file.suffix}.1")
            
            # Rename current file
            shutil.move(log_file, backup_file)
            
            # Create new empty file
            log_file.touch()
            
            # Compress old backup if needed
            if self._get_file_age(backup_file) >= self.compress_after_days:
                self._compress_backup(backup_file)
                
            # Clean up old backups
            self._cleanup_old_backups(log_file)
            
            return True
            
        except Exception as e:
            logging.error(f"Error rotating file {log_file}: {e}")
            return False

    def rotate_all(self) -> int:
        """Rotate all log files.
        
        Returns:
            Number of files rotated
        """
        count = 0
        for log_file in self.log_dir.glob("*.log"):
            if self.check_rotation(log_file) and self.rotate_file(log_file):
                count += 1
        return count

    def get_rotation_info(self, log_file: Union[str, Path]) -> Dict:
        """Get rotation information for a file.
        
        Args:
            log_file: Path to log file
            
        Returns:
            Dictionary with rotation info
        """
        log_file = Path(log_file)
        if not log_file.exists():
            return {
                "size": 0,
                "age_days": 0,
                "backup_count": 0,
                "needs_rotation": False
            }
            
        return {
            "size": self._get_file_size(log_file),
            "age_days": self._get_file_age(log_file),
            "backup_count": len(list(log_file.parent.glob(f"{log_file.stem}{log_file.suffix}.*"))),
            "needs_rotation": self.check_rotation(log_file)
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
