"""
Log Rotator Module
-----------------
Handles log file rotation and cleanup.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
import os
import shutil
import json
import logging
import gzip
import platform
from dataclasses import dataclass
from contextlib import contextmanager
import threading
import msvcrt  # Windows-specific file locking
import errno

logger = logging.getLogger(__name__)

# Import appropriate locking mechanism based on platform
if platform.system() == 'Windows':
    import msvcrt
else:
    import fcntl

@dataclass
class RotationConfig:
    """Configuration for log rotation."""
    log_dir: str = "logs"
    max_age_days: int = 7
    max_size_mb: int = 10
    compress_after_days: int = 1
    max_backups: int = 10

class LogRotator:
    """Handles log file rotation and cleanup."""
    
    def __init__(
        self,
        log_dir: str,
        max_age_days: int = 30,
        max_size_mb: int = 10,
        compress_after_days: int = 1,
        max_backups: int = 5
    ):
        """Initialize log rotator.
        
        Args:
            log_dir: Directory containing log files
            max_age_days: Maximum age of log files in days
            max_size_mb: Maximum size of log files in MB
            compress_after_days: Days after which to compress logs
            max_backups: Maximum number of backup files to keep
        """
        self.log_dir = Path(log_dir)
        self.max_age_days = max_age_days
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.compress_after_days = compress_after_days
        self.max_backups = max_backups
        self._lock = threading.Lock()
        self._file_locks: Dict[str, threading.Lock] = {}
    
    def _get_file_lock(self, file_path: str) -> threading.Lock:
        """Get or create a lock for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Thread lock for the file
        """
        with self._lock:
            if file_path not in self._file_locks:
                self._file_locks[file_path] = threading.Lock()
            return self._file_locks[file_path]
    
    def _ensure_log_directory(self) -> None:
        """Ensure log directory exists and is writable."""
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            # Test write access
            test_file = self.log_dir / ".test_write"
            test_file.touch()
            test_file.unlink()
        except (OSError, PermissionError) as e:
            logger.error(f"Failed to access log directory {self.log_dir}: {e}")
            raise
    
    def should_rotate(self, file_path: str) -> bool:
        """Check if a file should be rotated.
        
        Args:
            file_path: Path to the log file
            
        Returns:
            True if file should be rotated
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return False
            
            # Check file size
            if file_path.stat().st_size >= self.max_size_bytes:
                return True
            
            # Check file age
            file_age = datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)
            return file_age.days >= self.max_age_days
            
        except Exception as e:
            logger.error(f"Error checking if {file_path} should be rotated: {e}")
            return False
    
    def rotate_file(self, file_path: str) -> Optional[str]:
        """Rotate a log file.
        
        Args:
            file_path: Path to the log file
            
        Returns:
            Path to the rotated file, or None if rotation failed
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return None
            
            # Get file lock
            with self._get_file_lock(str(file_path)):
                # Create backup filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = file_path.parent / f"{file_path.stem}_{timestamp}{file_path.suffix}"
                
                # Move file to backup location
                shutil.move(str(file_path), str(backup_path))
                
                # Create new empty file
                file_path.touch()
                
                # Compress if needed
                if self.compress_after_days == 0:
                    self._compress_file(backup_path)
                
                return str(backup_path)
                
        except Exception as e:
            logger.error(f"Error rotating {file_path}: {e}")
            return None
    
    def _compress_file(self, file_path: Path) -> None:
        """Compress a log file.
        
        Args:
            file_path: Path to the file to compress
        """
        try:
            compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            file_path.unlink()
        except Exception as e:
            logger.error(f"Error compressing {file_path}: {e}")
    
    def cleanup_old_files(self) -> None:
        """Clean up old log files."""
        try:
            self._ensure_log_directory()
            
            # Get all log files
            log_files = list(self.log_dir.glob('*.log'))
            backup_files = list(self.log_dir.glob('*.log.*'))
            all_files = log_files + backup_files
            
            # Sort by modification time (oldest first)
            all_files.sort(key=lambda f: f.stat().st_mtime)
            
            # Keep only the newest max_backups files
            while len(all_files) > self.max_backups:
                file_to_remove = all_files.pop(0)
                try:
                    with self._get_file_lock(str(file_to_remove)):
                        file_to_remove.unlink()
                except Exception as e:
                    logger.error(f"Error removing old file {file_to_remove}: {e}")
            
            # Compress files older than compress_after_days
            if self.compress_after_days > 0:
                for file_path in all_files:
                    file_age = datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_age.days >= self.compress_after_days and not file_path.suffix.endswith('.gz'):
                        try:
                            with self._get_file_lock(str(file_path)):
                                self._compress_file(file_path)
                        except Exception as e:
                            logger.error(f"Error compressing old file {file_path}: {e}")
                            
        except Exception as e:
            logger.error(f"Error cleaning up old log files: {e}")
    
    def get_rotation_info(self) -> Dict[str, Any]:
        """Get current rotation settings.
        
        Returns:
            Dict containing rotation settings
        """
        return {
            "log_dir": str(self.log_dir),
            "max_age_days": self.max_age_days,
            "max_size_mb": self.max_size_bytes // (1024 * 1024),
            "compress_after_days": self.compress_after_days,
            "max_backups": self.max_backups
        }
    
    def reset(self) -> None:
        """Reset rotation settings to defaults."""
        self.max_age_days = 30
        self.max_size_bytes = 10 * 1024 * 1024
        self.compress_after_days = 1
        self.max_backups = 5 