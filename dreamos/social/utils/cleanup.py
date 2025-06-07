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
try:
    import win32file
    import win32con
    import pywintypes
except Exception:  # pragma: no cover - win32 modules unavailable on non-Windows
    win32file = None
    win32con = None
    pywintypes = None
import stat

logger = logging.getLogger(__name__)

class FileCleanup:
    """Handles safe file cleanup with proper lock handling."""
    
    def __init__(self):
        """Initialize cleanup utility."""
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
            
    def _force_close_handle(self, filepath: str) -> None:
        """Force close any open handles to a file on Windows.
        
        Args:
            filepath: Path to the file
        """
        if platform.system() != 'Windows':
            return
            
        try:
            # Try to open file with full access
            handle = win32file.CreateFile(
                str(filepath),
                win32con.GENERIC_READ | win32con.GENERIC_WRITE,
                0, None, win32con.OPEN_EXISTING,
                win32con.FILE_ATTRIBUTE_NORMAL | win32con.FILE_FLAG_DELETE_ON_CLOSE,
                None
            )
            win32file.CloseHandle(handle)
        except pywintypes.error as e:
            if e.winerror != 32:  # Not a sharing violation
                logger.warning(f"Error closing handle for {filepath}: {e}")
            
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
                    self._force_close_handle(file_path)
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
            
    def cleanup_directory(self, directory: str, pattern: str = "*", max_retries: int = 5) -> bool:
        """Clean up files in a directory matching a pattern.
        
        Args:
            directory: Directory to clean up
            pattern: File pattern to match
            max_retries: Maximum number of retries per file
            
        Returns:
            bool: True if all files were removed, False otherwise
        """
        try:
            directory = Path(directory)
            if not directory.exists():
                return True
                
            # Handle symlinks
            if directory.is_symlink():
                directory.unlink()
                return True
                
            # Try to remove directory contents first
            success = True
            for item in directory.glob(pattern):
                try:
                    if item.is_file():
                        # Wait for file to be unlocked on Windows
                        if platform.system() == 'Windows':
                            retries = 3
                            while retries > 0 and self._is_file_locked(item):
                                time.sleep(0.1)
                                retries -= 1
                        if not self.safe_remove(item, max_retries):
                            success = False
                    else:
                        # Try to change permissions first
                        if platform.system() == 'Windows':
                            os.chmod(str(item), stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
                        else:
                            os.chmod(str(item), 0o777)
                        time.sleep(0.1)  # Give time for permission change to take effect
                        shutil.rmtree(item)
                except Exception as e:
                    logger.warning(f"Failed to remove {item}: {str(e)}")
                    success = False
            
            # Then try to remove the directory itself
            try:
                if platform.system() == 'Windows':
                    # Wait a bit for Windows to release the directory
                    time.sleep(0.1)
                directory.rmdir()
            except Exception as e:
                logger.warning(f"Failed to remove directory {directory}: {str(e)}")
                success = False
                
            return success
            
        except Exception as e:
            logger.error(f"Error cleaning up directory {directory}: {e}")
            return False
            
    def cleanup_temp_files(self, directory: str, max_age_hours: int = 24, max_retries: int = 5) -> bool:
        """Clean up temporary files older than max_age_hours.
        
        Args:
            directory: Directory containing temp files
            max_age_hours: Maximum age of files in hours
            max_retries: Maximum number of retries per file
            
        Returns:
            bool: True if all files were removed, False otherwise
        """
        try:
            directory = Path(directory)
            if not directory.exists():
                return True
                
            cutoff_time = time.time() - (max_age_hours * 3600)
            success = True
            
            for file_path in directory.glob("*"):
                try:
                    if file_path.stat().st_mtime < cutoff_time:
                        if not self.safe_remove(file_path, max_retries):
                            success = False
                except Exception:
                    continue
                    
            return success
            
        except Exception as e:
            logger.error(f"Error cleaning up temp files in {directory}: {e}")
            return False 