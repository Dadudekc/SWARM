"""
Cleanup Utility Module
--------------------
Handles safe file cleanup with proper lock handling.
"""

import os
import logging
import platform
import threading
import time
import shutil
from pathlib import Path
import sys
from datetime import datetime, timedelta
try:
    import win32file
    import win32con
    import pywintypes
except Exception:  # pragma: no cover - win32 modules unavailable on non-Windows
    win32file = None
    win32con = None
    pywintypes = None
import stat

from .base import BaseUtils

logger = logging.getLogger(__name__)

class FileCleanup(BaseUtils):
    """Handles safe file cleanup with proper lock handling."""
    
    def __init__(self, config: dict = None):
        """Initialize cleanup utility."""
        super().__init__(config or {})
        self._lock = threading.RLock()
        self._file_locks = {}
        
    def _is_file_locked(self, filepath: str) -> bool:
        """Check if a file is locked on Windows.
        
        Args:
            filepath: Path to the file to check
            
        Returns:
            bool: True if file is locked, False otherwise
        """
        if platform.system() != 'Windows':
            return False
            
        try:
            filepath = str(filepath)
            GENERIC_READ = 0x80000000
            FILE_SHARE_READ = 0x00000001
            OPEN_EXISTING = 3
            INVALID_HANDLE_VALUE = -1
            
            handle = win32file.CreateFile(
                filepath,
                GENERIC_READ,
                FILE_SHARE_READ,
                None,
                OPEN_EXISTING,
                0,
                None
            )
            
            if handle == INVALID_HANDLE_VALUE:
                return True
                
            win32file.CloseHandle(handle)
            return False
            
        except Exception as e:
            logger.error(f"Error checking file lock: {e}")
            return True
            
    def _force_close_handle(self, file_path: Path) -> bool:
        """Force close any open handles to a file on Windows.
        
        Args:
            file_path: Path to the file
            
        Returns:
            bool: True if handle was closed successfully
        """
        if not sys.platform == "win32":
            return True
        
        try:
            # Try to open file with full access
            handle = win32file.CreateFile(
                str(file_path),
                win32con.GENERIC_READ | win32con.GENERIC_WRITE,
                0,  # No sharing
                None,
                win32con.OPEN_EXISTING,
                win32con.FILE_ATTRIBUTE_NORMAL,
                None
            )
            
            # Close handle
            win32file.CloseHandle(handle)
            return True
            
        except Exception as e:
            logging.warning(f"Error closing file handle: {e}")
            return False

    def _wait_for_file_unlock(self, file_path: str, max_retries: int = 5) -> bool:
        """Wait for file to be unlocked.
        
        Args:
            file_path: Path to file
            max_retries: Maximum number of retries
            
        Returns:
            bool: True if file is unlocked, False otherwise
        """
        for _ in range(max_retries):
            try:
                if platform.system() == 'Windows':
                    # First check if file is locked
                    if not self._is_file_locked(file_path):
                        return True
                        
                    # Try to force close any open handles
                    self._force_close_handle(Path(file_path))
                    time.sleep(0.2)  # Wait for handle to be released
                    
                    # Check again if file is unlocked
                    if not self._is_file_locked(file_path):
                        return True
                else:
                    with open(file_path, 'r'):
                        return True
            except (OSError, pywintypes.error) as e:
                if platform.system() == 'Windows' and isinstance(e, pywintypes.error):
                    if e.winerror != 32:  # Not a sharing violation
                        return False
                time.sleep(0.2)
        return False
        
    def safe_remove(self, path: str, max_retries: int = 5) -> bool:
        """Safely remove a file with proper handle cleanup.
        
        Args:
            path: Path to file to remove
            max_retries: Maximum number of retries
            
        Returns:
            bool: True if file was removed, False otherwise
        """
        try:
            path = Path(path)
            if not path.exists():
                return True
                
            if path.is_file():
                # Wait for file to be unlocked on Windows
                if platform.system() == 'Windows':
                    retries = 5
                    while retries > 0 and self._is_file_locked(path):
                        time.sleep(0.2)
                        retries -= 1
                        
                try:
                    # Try to change permissions first
                    if platform.system() == 'Windows':
                        os.chmod(str(path), stat.S_IWRITE | stat.S_IREAD)
                    else:
                        os.chmod(str(path), 0o666)
                    time.sleep(0.1)  # Give time for permission change to take effect
                    path.unlink()
                    return True
                except PermissionError:
                    # Try to force close any open handles on Windows
                    if platform.system() == 'Windows':
                        self._force_close_handle(path)
                        time.sleep(0.2)  # Wait for handle to be released
                    path.unlink()
                    return True
            else:
                try:
                    # Try to change permissions first
                    if platform.system() == 'Windows':
                        os.chmod(str(path), stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
                    else:
                        os.chmod(str(path), 0o777)
                    time.sleep(0.1)  # Give time for permission change to take effect
                    shutil.rmtree(path)
                    return True
                except PermissionError:
                    # Try to force close any open handles on Windows
                    if platform.system() == 'Windows':
                        self._force_close_handle(path)
                        time.sleep(0.2)  # Wait for handle to be released
                    shutil.rmtree(path)
                    return True
        except Exception as e:
            logger.warning(f"Failed to remove {path}: {str(e)}")
            return False
            
    def cleanup_directory(self, directory: Path, pattern: str = "*") -> bool:
        """Clean up files in a directory matching a pattern.
        
        Args:
            directory: Directory to clean up
            pattern: File pattern to match
            
        Returns:
            bool: True if cleanup was successful
        """
        try:
            # Check if directory exists
            if not directory.exists():
                return True
                
            # Get files matching pattern
            files = list(directory.glob(pattern))
            
            # Remove files
            for file in files:
                try:
                    if file.is_file():
                        file.unlink()
                    elif file.is_dir():
                        shutil.rmtree(file)
                except Exception as e:
                    logging.error(f"Error removing {file}: {e}")
                    return False
                    
            return True
            
        except Exception as e:
            logging.error(f"Error cleaning up directory {directory}: {e}")
            return False
            
    def cleanup_temp_files(self, directory: Path, max_age_days: int = 7) -> bool:
        """Clean up temporary files in a directory.
        
        Args:
            directory: Directory to clean up
            max_age_days: Maximum age of files in days
            
        Returns:
            bool: True if cleanup was successful
        """
        try:
            # Common temporary file extensions
            temp_extensions = {".tmp", ".temp", ".bak", ".old", ".log"}
            
            # Get all files
            files = list(directory.glob("*"))
            
            # Filter temp files
            temp_files = []
            for file in files:
                if file.is_file():
                    # Check extension
                    if file.suffix.lower() in temp_extensions:
                        temp_files.append(file)
                    # Check name
                    elif "temp" in file.name.lower() or "tmp" in file.name.lower():
                        temp_files.append(file)
                    
            # Remove old files
            cutoff_time = datetime.now() - timedelta(days=max_age_days)
            for file in temp_files:
                try:
                    if datetime.fromtimestamp(file.stat().st_mtime) < cutoff_time:
                        file.unlink()
                except Exception as e:
                    logging.error(f"Error removing temp file {file}: {e}")
                    return False
                    
            return True
            
        except Exception as e:
            logging.error(f"Error cleaning up temp files in {directory}: {e}")
            return False 
