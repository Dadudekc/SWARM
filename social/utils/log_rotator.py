"""
Log Rotator Module
-----------------
Handles log file rotation and compression.
"""

import os
import time
import gzip
import shutil
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path
import logging
import platform
import stat
import win32file
import win32con
import pywintypes
import ctypes
from ctypes import wintypes
import win32api
import win32security
import win32process
import threading

from .log_types import RotationConfig

logger = logging.getLogger(__name__)

class LogRotator:
    """Handles log file rotation and compression.
    
    This class manages:
    - Size-based rotation
    - Age-based rotation
    - Compression of old logs
    - Cleanup of expired logs
    """
    
    def __init__(self, config: RotationConfig):
        """Initialize rotator with configuration.
        
        Args:
            config: Rotation configuration
        """
        self.config = config
        self._validate_config()
        self._lock = threading.RLock()
        self._file_locks = {}
        
    def _validate_config(self) -> None:
        """Validate rotation configuration."""
        if self.config.max_size_mb <= 0:
            raise ValueError("max_size_mb must be positive")
        if self.config.max_files < 0:
            raise ValueError("max_files cannot be negative")
        if self.config.max_age_days <= 0:
            raise ValueError("max_age_days must be positive")
        if self.config.compress_after_days <= 0:
            raise ValueError("compress_after_days must be positive")
            
    def should_rotate(self, file_path: str) -> bool:
        """Check if file should be rotated based on size.
        
        Args:
            file_path: Path to log file
            
        Returns:
            bool: True if file should be rotated
        """
        try:
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            return size_mb >= self.config.max_size_mb
        except OSError as e:
            logger.error(f"Error checking file size: {e}")
            return False
            
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
            
            handle = ctypes.windll.kernel32.CreateFileW(
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
                
            ctypes.windll.kernel32.CloseHandle(handle)
            return False
        except Exception:
            return True
            
    def _force_close_handle(self, filepath: str) -> None:
        """Force close any open handles to a file on Windows.
        
        Args:
            filepath: Path to the file
        """
        if platform.system() != 'Windows':
            return
            
        try:
            # Try to open file with full access and delete on close
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
                    with open(file_path, 'a'):
                        return True
            except (OSError, pywintypes.error) as e:
                if platform.system() == 'Windows' and isinstance(e, pywintypes.error):
                    if e.winerror != 32:  # Not a sharing violation
                        return False
                time.sleep(0.2)
        return False
            
    def _safe_remove(self, path: str) -> bool:
        """Safely remove a file with proper handle cleanup.
        
        Args:
            path: Path to file to remove
            
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
                        # Also try to take ownership if needed
                        try:
                            security_info = win32security.GetFileSecurity(
                                str(path), win32security.OWNER_SECURITY_INFORMATION
                            )
                            owner_sid = security_info.GetSecurityDescriptorOwner()
                            if owner_sid:
                                # Get current process token
                                process_handle = win32api.GetCurrentProcess()
                                token_handle = win32security.OpenProcessToken(
                                    process_handle,
                                    win32security.TOKEN_ADJUST_PRIVILEGES | win32security.TOKEN_QUERY
                                )
                                # Enable SeTakeOwnershipPrivilege
                                privilege_id = win32security.LookupPrivilegeValue(
                                    None, win32security.SE_TAKE_OWNERSHIP_NAME
                                )
                                win32security.AdjustTokenPrivileges(
                                    token_handle, 0, [(privilege_id, win32security.SE_PRIVILEGE_ENABLED)]
                                )
                                # Set new owner
                                win32security.SetFileSecurity(
                                    str(path),
                                    win32security.OWNER_SECURITY_INFORMATION,
                                    security_info
                                )
                        except Exception as e:
                            logger.warning(f"Failed to take ownership of {path}: {e}")
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
                        # Also try to take ownership if needed
                        try:
                            security_info = win32security.GetFileSecurity(
                                str(path), win32security.OWNER_SECURITY_INFORMATION
                            )
                            owner_sid = security_info.GetSecurityDescriptorOwner()
                            if owner_sid:
                                # Get current process token
                                process_handle = win32api.GetCurrentProcess()
                                token_handle = win32security.OpenProcessToken(
                                    process_handle,
                                    win32security.TOKEN_ADJUST_PRIVILEGES | win32security.TOKEN_QUERY
                                )
                                # Enable SeTakeOwnershipPrivilege
                                privilege_id = win32security.LookupPrivilegeValue(
                                    None, win32security.SE_TAKE_OWNERSHIP_NAME
                                )
                                win32security.AdjustTokenPrivileges(
                                    token_handle, 0, [(privilege_id, win32security.SE_PRIVILEGE_ENABLED)]
                                )
                                # Set new owner
                                win32security.SetFileSecurity(
                                    str(path),
                                    win32security.OWNER_SECURITY_INFORMATION,
                                    security_info
                                )
                        except Exception as e:
                            logger.warning(f"Failed to take ownership of {path}: {e}")
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
            
    def _cleanup_directory(self, directory: str) -> None:
        """Clean up a directory and its contents.
        
        Args:
            directory: Path to directory to clean up
        """
        try:
            directory = Path(directory)
            if not directory.exists():
                return
                
            # Handle symlinks
            if directory.is_symlink():
                directory.unlink()
                return
                
            # Try to remove directory contents first
            for item in directory.iterdir():
                try:
                    if item.is_file():
                        # Wait for file to be unlocked on Windows
                        if platform.system() == 'Windows':
                            retries = 3
                            while retries > 0 and self._is_file_locked(item):
                                time.sleep(0.1)
                                retries -= 1
                        self._safe_remove(item)
                    else:
                        shutil.rmtree(item)
                except Exception as e:
                    logger.warning(f"Failed to remove {item}: {str(e)}")
            
            # Then try to remove the directory itself
            try:
                if platform.system() == 'Windows':
                    # Wait a bit for Windows to release the directory
                    time.sleep(0.1)
                    # Try to take ownership if needed
                    try:
                        security_info = win32security.GetFileSecurity(
                            str(directory), win32security.OWNER_SECURITY_INFORMATION
                        )
                        owner_sid = security_info.GetSecurityDescriptorOwner()
                        if owner_sid:
                            # Get current process token
                            process_handle = win32api.GetCurrentProcess()
                            token_handle = win32security.OpenProcessToken(
                                process_handle,
                                win32security.TOKEN_ADJUST_PRIVILEGES | win32security.TOKEN_QUERY
                            )
                            # Enable SeTakeOwnershipPrivilege
                            privilege_id = win32security.LookupPrivilegeValue(
                                None, win32security.SE_TAKE_OWNERSHIP_NAME
                            )
                            win32security.AdjustTokenPrivileges(
                                token_handle, 0, [(privilege_id, win32security.SE_PRIVILEGE_ENABLED)]
                            )
                            # Set new owner
                            win32security.SetFileSecurity(
                                str(directory),
                                win32security.OWNER_SECURITY_INFORMATION,
                                security_info
                            )
                    except Exception as e:
                        logger.warning(f"Failed to take ownership of {directory}: {e}")
                directory.rmdir()
            except Exception as e:
                logger.warning(f"Failed to remove directory {directory}: {str(e)}")
        except Exception as e:
            logger.warning(f"Failed to clean up directory {directory}: {str(e)}")
            
    def rotate(self, file_path: str) -> Optional[str]:
        """Rotate a log file.
        
        Args:
            file_path: Path to log file to rotate
            
        Returns:
            Optional[str]: Path to new log file if rotation successful, None otherwise
        """
        with self._lock:
            try:
                file_path = str(file_path)
                if not os.path.exists(file_path):
                    return None
                    
                # Wait for file to be unlocked
                if not self._wait_for_file_unlock(file_path):
                    logger.error(f"Could not unlock file {file_path} for rotation")
                    return None
                    
                # Generate new filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_name = os.path.splitext(file_path)[0]
                new_name = f"{base_name}.{timestamp}.log"
                
                # Try to rename file
                try:
                    # First try to change permissions
                    if platform.system() == 'Windows':
                        os.chmod(file_path, stat.S_IWRITE | stat.S_IREAD)
                        # Try to take ownership if needed
                        try:
                            security_info = win32security.GetFileSecurity(
                                file_path, win32security.OWNER_SECURITY_INFORMATION
                            )
                            owner_sid = security_info.GetSecurityDescriptorOwner()
                            if owner_sid:
                                # Get current process token
                                process_handle = win32api.GetCurrentProcess()
                                token_handle = win32security.OpenProcessToken(
                                    process_handle,
                                    win32security.TOKEN_ADJUST_PRIVILEGES | win32security.TOKEN_QUERY
                                )
                                # Enable SeTakeOwnershipPrivilege
                                privilege_id = win32security.LookupPrivilegeValue(
                                    None, win32security.SE_TAKE_OWNERSHIP_NAME
                                )
                                win32security.AdjustTokenPrivileges(
                                    token_handle, 0, [(privilege_id, win32security.SE_PRIVILEGE_ENABLED)]
                                )
                                # Set new owner
                                win32security.SetFileSecurity(
                                    file_path,
                                    win32security.OWNER_SECURITY_INFORMATION,
                                    security_info
                                )
                        except Exception as e:
                            logger.warning(f"Failed to take ownership of {file_path}: {e}")
                    else:
                        os.chmod(file_path, 0o666)
                    
                    # Wait a bit for permissions to take effect
                    time.sleep(0.1)
                    
                    # Try to rename
                    os.rename(file_path, new_name)
                    
                    # Create new empty log file
                    with open(file_path, 'w') as f:
                        pass
                    
                    # Clean up old backups
                    self._cleanup_old_backups(file_path)
                    
                    return new_name
                    
                except (OSError, PermissionError) as e:
                    logger.error(f"Error rotating log file {file_path}: {e}")
                    return None
                    
            except Exception as e:
                logger.error(f"Unexpected error during log rotation: {e}")
                return None

    def _cleanup_old_backups(self, current_file: str) -> None:
        """Clean up old backup files.
        
        Args:
            current_file: Path to current log file
        """
        try:
            base_name = os.path.splitext(current_file)[0]
            backup_dir = os.path.dirname(current_file)
            
            # Get all backup files
            backup_files = []
            for file in os.listdir(backup_dir):
                if file.startswith(os.path.basename(base_name)) and file.endswith('.log'):
                    full_path = os.path.join(backup_dir, file)
                    if full_path != current_file:
                        backup_files.append(full_path)
            
            # Sort by modification time (oldest first)
            backup_files.sort(key=lambda x: os.path.getmtime(x))
            
            # Remove excess files
            while len(backup_files) > self.config.max_files:
                oldest = backup_files.pop(0)
                try:
                    if platform.system() == 'Windows':
                        # Try to change permissions first
                        os.chmod(oldest, stat.S_IWRITE | stat.S_IREAD)
                        # Try to take ownership if needed
                        try:
                            security_info = win32security.GetFileSecurity(
                                oldest, win32security.OWNER_SECURITY_INFORMATION
                            )
                            owner_sid = security_info.GetSecurityDescriptorOwner()
                            if owner_sid:
                                # Get current process token
                                process_handle = win32api.GetCurrentProcess()
                                token_handle = win32security.OpenProcessToken(
                                    process_handle,
                                    win32security.TOKEN_ADJUST_PRIVILEGES | win32security.TOKEN_QUERY
                                )
                                # Enable SeTakeOwnershipPrivilege
                                privilege_id = win32security.LookupPrivilegeValue(
                                    None, win32security.SE_TAKE_OWNERSHIP_NAME
                                )
                                win32security.AdjustTokenPrivileges(
                                    token_handle, 0, [(privilege_id, win32security.SE_PRIVILEGE_ENABLED)]
                                )
                                # Set new owner
                                win32security.SetFileSecurity(
                                    oldest,
                                    win32security.OWNER_SECURITY_INFORMATION,
                                    security_info
                                )
                        except Exception as e:
                            logger.warning(f"Failed to take ownership of {oldest}: {e}")
                    else:
                        os.chmod(oldest, 0o666)
                    
                    # Wait a bit for permissions to take effect
                    time.sleep(0.1)
                    
                    # Try to remove
                    os.remove(oldest)
                except Exception as e:
                    logger.error(f"Error removing old backup {oldest}: {e}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
            
    def compress_old_logs(self) -> None:
        """Compress log files older than compress_after_days."""
        try:
            backup_dir = self.config.backup_dir
            if not backup_dir:
                return
                
            cutoff_time = time.time() - (self.config.compress_after_days * 86400)
            
            for f in os.listdir(backup_dir):
                if f.endswith('.gz'):
                    continue
                    
                file_path = os.path.join(backup_dir, f)
                if os.path.getmtime(file_path) < cutoff_time:
                    try:
                        # Force close any open handles
                        self._force_close_handle(file_path)
                        
                        # Wait for file to be unlocked
                        if not self._wait_for_file_unlock(file_path):
                            logger.warning(f"Could not unlock file {file_path} for compression")
                            continue
                            
                        # Compress file
                        with open(file_path, 'rb') as f_in:
                            with gzip.open(file_path + '.gz', 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                                
                        # Remove original file
                        if not self._safe_remove(file_path):
                            logger.warning(f"Could not remove original file after compression: {file_path}")
                    except (OSError, PermissionError) as e:
                        logger.warning(f"Could not compress file {file_path}: {e}")
                        
        except OSError as e:
            logger.error(f"Error compressing old logs: {e}")
            
    def get_rotation_info(self) -> Dict[str, Any]:
        """Get current rotation configuration and stats.
        
        Returns:
            Dict[str, Any]: Rotation information
        """
        return {
            'max_size_mb': self.config.max_size_mb,
            'max_files': self.config.max_files,
            'max_age_days': self.config.max_age_days,
            'compress_after_days': self.config.compress_after_days,
            'backup_dir': self.config.backup_dir
        }

    def rotate_if_needed(self, file_path: str) -> Optional[str]:
        """Check if rotation is needed and perform it if necessary.
        
        Args:
            file_path: Path to log file
            
        Returns:
            Optional[str]: Path to new log file if rotated, None otherwise
        """
        if not os.path.exists(file_path):
            return None
            
        if self.should_rotate(file_path):
            return self.rotate(file_path)
        return None 