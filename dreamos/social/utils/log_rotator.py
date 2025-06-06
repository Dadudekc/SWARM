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
    
    def _rotate_file(self, filepath: Path) -> None:
        """Rotate a single log file.
        
        Args:
            filepath: Path to log file
        """
        try:
            # Create backup directory if it doesn't exist
            backup_dir = self.log_dir / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{filepath.stem}_{timestamp}{filepath.suffix}"
            backup_path = backup_dir / backup_name
            
            # Move current file to backup
            shutil.move(str(filepath), str(backup_path))
            
            # Create new empty file
            filepath.touch()
            
            logger.info(f"Rotated log file {filepath} to {backup_path}")
            
        except Exception as e:
            logger.error(f"Error rotating file {filepath}: {e}")
    
    def _cleanup_old_backups(self) -> None:
        """Clean up old backup files."""
        try:
            backup_dir = self.log_dir / "backups"
            if not backup_dir.exists():
                return
                
            # Get all backup files
            backup_files = sorted(
                backup_dir.glob("*_*.*"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            # Remove excess backups
            for backup_file in backup_files[self.backup_count:]:
                try:
                    backup_file.unlink()
                    logger.info(f"Removed old backup file {backup_file}")
                except OSError as e:
                    logger.error(f"Error removing backup file {backup_file}: {e}")
                    
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
            backup_dir = self.log_dir / "backups"
            backup_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{path.stem}_{timestamp}{path.suffix}"
            backup_path = backup_dir / backup_name
            shutil.move(str(path), str(backup_path))
            path.touch()
            logger.info(f"Rotated log file {path} to {backup_path}")
            return str(backup_path)
        except Exception as e:
            logger.error(f"Error rotating file {path}: {e}")
            return "" 