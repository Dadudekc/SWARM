"""
Windows-specific file handling utilities for fixing quarantined log tests.
Provides safe wrappers for file operations, locking, and permissions.
"""

import os
import time
import msvcrt
import logging
import tempfile
from pathlib import Path
from typing import Optional, Callable, Any, BinaryIO, TextIO, Union
from contextlib import contextmanager
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MAX_RETRIES = 5
RETRY_DELAY = 0.1
FILE_LOCK_TIMEOUT = 5.0

class FileOperationError(Exception):
    """Base exception for file operation errors."""
    pass

class FileLockError(FileOperationError):
    """Raised when file locking fails."""
    pass

class FilePermissionError(FileOperationError):
    """Raised when file permission checks fail."""
    pass

def normalize_path(path: Union[str, Path]) -> Path:
    """Normalize path for Windows compatibility."""
    return Path(path).resolve()

def ensure_dir(path: Union[str, Path]) -> None:
    """Ensure directory exists with proper permissions."""
    path = normalize_path(path)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    if not os.access(path, os.W_OK):
        raise FilePermissionError(f"No write access to directory: {path}")

@contextmanager
def safe_file_handle(
    filepath: Union[str, Path],
    mode: str = 'r',
    encoding: str = 'utf-8',
    retries: int = MAX_RETRIES,
    delay: float = RETRY_DELAY
) -> Union[TextIO, BinaryIO]:
    """
    Safe file handle context manager with retry logic.
    
    Args:
        filepath: Path to file
        mode: File open mode
        encoding: File encoding (for text mode)
        retries: Number of retry attempts
        delay: Delay between retries in seconds
    """
    filepath = normalize_path(filepath)
    ensure_dir(filepath.parent)
    
    handle = None
    last_error = None
    
    for attempt in range(retries):
        try:
            if 'b' in mode:
                handle = open(filepath, mode)
            else:
                handle = open(filepath, mode, encoding=encoding)
            break
        except (IOError, PermissionError) as e:
            last_error = e
            if attempt < retries - 1:
                time.sleep(delay)
                continue
            raise FileOperationError(f"Failed to open file after {retries} attempts: {e}")
    
    try:
        yield handle
    finally:
        if handle:
            try:
                handle.close()
            except Exception as e:
                logger.error(f"Error closing file handle: {e}")

@contextmanager
def file_lock(
    filepath: Union[str, Path],
    timeout: float = FILE_LOCK_TIMEOUT
) -> None:
    """
    Windows-specific file locking context manager.
    
    Args:
        filepath: Path to file
        timeout: Maximum time to wait for lock
    """
    filepath = normalize_path(filepath)
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            with open(filepath, 'r+b') as f:
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                try:
                    yield
                finally:
                    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                return
        except IOError:
            time.sleep(RETRY_DELAY)
    
    raise FileLockError(f"Could not acquire lock on {filepath} after {timeout}s")

def with_retry(
    max_attempts: int = MAX_RETRIES,
    delay: float = RETRY_DELAY,
    exceptions: tuple = (IOError, PermissionError)
) -> Callable:
    """
    Decorator for retrying operations with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Base delay between retries
        exceptions: Tuple of exceptions to catch and retry
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay * (2 ** attempt))
                        continue
            raise FileOperationError(f"Operation failed after {max_attempts} attempts: {last_error}")
        return wrapper
    return decorator

def safe_write(
    filepath: Union[str, Path],
    data: Union[str, bytes],
    mode: str = 'w',
    encoding: str = 'utf-8'
) -> None:
    """
    Safely write data to file with proper locking and error handling.
    
    Args:
        filepath: Path to file
        data: Data to write
        mode: File open mode
        encoding: File encoding (for text mode)
    """
    filepath = normalize_path(filepath)
    ensure_dir(filepath.parent)
    
    with file_lock(filepath):
        with safe_file_handle(filepath, mode, encoding) as f:
            f.write(data)

def safe_read(
    filepath: Union[str, Path],
    mode: str = 'r',
    encoding: str = 'utf-8'
) -> Union[str, bytes]:
    """
    Safely read data from file with proper locking and error handling.
    
    Args:
        filepath: Path to file
        mode: File open mode
        encoding: File encoding (for text mode)
    """
    filepath = normalize_path(filepath)
    
    with file_lock(filepath):
        with safe_file_handle(filepath, mode, encoding) as f:
            return f.read()

def get_temp_log_dir() -> Path:
    """Get temporary directory for log files with proper permissions."""
    temp_dir = Path(tempfile.gettempdir()) / 'dream_os_logs'
    ensure_dir(temp_dir)
    return temp_dir

def check_file_permissions(filepath: Union[str, Path]) -> bool:
    """
    Check if file has proper read/write permissions.
    
    Args:
        filepath: Path to file
    """
    filepath = normalize_path(filepath)
    return os.access(filepath, os.R_OK | os.W_OK)

def rotate_log_file(
    filepath: Union[str, Path],
    max_size: int,
    backup_count: int = 5
) -> None:
    """
    Safely rotate log file when it exceeds max_size.
    
    Args:
        filepath: Path to log file
        max_size: Maximum file size in bytes
        backup_count: Number of backup files to keep
    """
    filepath = normalize_path(filepath)
    
    if not filepath.exists():
        return
    
    try:
        size = filepath.stat().st_size
        if size < max_size:
            return
            
        # Rotate existing backups
        for i in range(backup_count - 1, 0, -1):
            old = filepath.with_suffix(f'.{i}')
            new = filepath.with_suffix(f'.{i + 1}')
            if old.exists():
                if new.exists():
                    new.unlink()
                old.rename(new)
        
        # Rotate current file
        if filepath.with_suffix('.1').exists():
            filepath.with_suffix('.1').unlink()
        filepath.rename(filepath.with_suffix('.1'))
        
    except Exception as e:
        logger.error(f"Error rotating log file {filepath}: {e}")
        raise FileOperationError(f"Failed to rotate log file: {e}") 