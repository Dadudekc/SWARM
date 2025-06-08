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
    
    def __init__(
        self,
        config: Union[str, RotationConfig],
        max_size_mb: int = 100,
        max_age_days: int = 30,
        backup_count: int = 5
    ):
        """Initialize log rotator.
        
        Args:
            config: Either a log directory path or a RotationConfig object
            max_size_mb: Maximum size of log files in MB (ignored if config is RotationConfig)
            max_age_days: Maximum age of log files in days (ignored if config is RotationConfig)
            backup_count: Number of backup files to keep (ignored if config is RotationConfig)
        """
        if isinstance(config, str):
            self.log_dir = Path(config)
            self.max_size_bytes = max_size_mb * 1024 * 1024
            self.max_age_seconds = max_age_days * 24 * 60 * 60
            self.backup_count = backup_count
        else:
            self.log_dir = Path(config.backup_dir or "logs")
            # Fallback for max_bytes if not present
            self.max_size_bytes = getattr(config, 'max_bytes', config.max_size_mb * 1024 * 1024)
            self.max_age_seconds = config.max_age_days * 24 * 60 * 60
            self.backup_count = config.max_files
        
        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_file_size(self, filepath: Path) -> int:
        """Get file size in bytes.
        
        Args:
            filepath: Path to file
            
        Returns:
            int: File size in bytes
        """
        try:
            return filepath.stat().st_size
        except OSError as e:
            logger.error(f"Error getting file size for {filepath}: {e}")
            return 0
    
    def _get_file_age(self, filepath: Path) -> float:
        """Get file age in seconds.
        
        Args:
            filepath: Path to file
            
        Returns:
            float: File age in seconds
        """
        try:
            return time.time() - filepath.stat().st_mtime
        except OSError as e:
            logger.error(f"Error getting file age for {filepath}: {e}")
            return 0
    
    def _rotate_file(self, file_path: Path) -> bool:
        """Rotate a single log file.
        
        Args:
            file_path: Path to the log file to rotate
            
        Returns:
            bool: True if rotation was successful
        """
        try:
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            backup_path = file_path.parent / f"{file_path.stem}_{timestamp}{file_path.suffix}"
            
            # Move original file to backup path
            file_path.rename(backup_path)
            
            # Create new empty file
            file_path.touch()
            
            # Ensure file is empty
            file_path.write_text("")
            
            logger.info(f"Rotated log file {file_path} to {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error rotating file {file_path}: {e}")
            return False
    
    def _cleanup_old_backups(self) -> None:
        """Clean up old backup files."""
        try:
            # Get all backup files with timestamp in name
            backup_files = []
            for file in self.log_dir.glob(f"*_*_*{self.file_suffix}"):
                if "_" in file.stem:  # Ensure it's a backup file
                    backup_files.append(file)
            
            # Sort by modification time
            backup_files.sort(key=lambda x: x.stat().st_mtime)
            
            # Keep only the most recent files up to backup_count
            while len(backup_files) > self.backup_count:
                old_file = backup_files.pop(0)
                try:
                    old_file.unlink()
                    logger.info(f"Removed old backup file: {old_file}")
                except Exception as e:
                    logger.error(f"Error removing old backup file {old_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
    
    def check_rotation(self, filepath: Path) -> bool:
        """Check if a file needs rotation.
        
        Args:
            filepath: Path to log file
            
        Returns:
            bool: True if file was rotated
        """
        if not filepath.exists():
            return False
            
        try:
            # Check file size
            if self._get_file_size(filepath) >= self.max_size_bytes:
                self._rotate_file(filepath)
                return True
                
            # Check file age
            if self._get_file_age(filepath) >= self.max_age_seconds:
                self._rotate_file(filepath)
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error checking rotation for {filepath}: {e}")
            return False
    
    def rotate_all(self) -> None:
        """Rotate all log files that need rotation."""
        try:
            # Get all log files
            log_files = list(self.log_dir.glob("*.json"))
            
            # Check each file
            for log_file in log_files:
                self.check_rotation(log_file)
                
            # Clean up old backups
            self._cleanup_old_backups()
            
        except Exception as e:
            logger.error(f"Error rotating all log files: {e}")
    
    def get_rotation_info(self) -> Dict[str, Any]:
        """Get information about log rotation status.
        
        Returns:
            Dict[str, Any]: Rotation status information
        """
        info = {
            "log_dir": str(self.log_dir),
            "max_size_mb": self.max_size_bytes / (1024 * 1024),
            "max_age_days": self.max_age_seconds / (24 * 60 * 60),
            "backup_count": self.backup_count,
            "files": []
        }
        
        try:
            # Get all log files
            log_files = list(self.log_dir.glob("*.json"))
            
            for log_file in log_files:
                file_info = {
                    "path": str(log_file),
                    "size_mb": self._get_file_size(log_file) / (1024 * 1024),
                    "age_days": self._get_file_age(log_file) / (24 * 60 * 60),
                    "needs_rotation": False
                }
                
                # Check if file needs rotation
                if (file_info["size_mb"] >= info["max_size_mb"] or
                    file_info["age_days"] >= info["max_age_days"]):
                    file_info["needs_rotation"] = True
                    
                info["files"].append(file_info)
                
            # Get backup info
            backup_dir = self.log_dir / "backups"
            if backup_dir.exists():
                backup_files = list(backup_dir.glob("*_*.*"))
                info["backup_count"] = len(backup_files)
                info["backup_size_mb"] = sum(
                    f.stat().st_size for f in backup_files
                ) / (1024 * 1024)
                
            return info
            
        except Exception as e:
            logger.error(f"Error getting rotation info: {e}")
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
