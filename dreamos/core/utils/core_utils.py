"""
Core Utilities
------------
Core utility functions for Dream.OS system.
"""

import os
import tempfile
import json
import shutil
import logging
import time
import asyncio
import yaml
from typing import Any, Optional, Dict, Tuple, Union, Callable, TypeVar, List
from pathlib import Path
from datetime import datetime
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')

class ErrorTracker:
    """Track and manage operation errors."""
    
    def __init__(self, max_errors: int = 100):
        self.errors: List[Dict[str, Any]] = []
        self.max_errors = max_errors
    
    def add_error(
        self,
        error: Exception,
        operation: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add an error to the tracker.
        
        Args:
            error: Exception that occurred
            operation: Operation that failed
            context: Optional context data
        """
        error_data = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context or {}
        }
        
        self.errors.append(error_data)
        
        # Trim old errors if over limit
        if len(self.errors) > self.max_errors:
            self.errors = self.errors[-self.max_errors:]
    
    def get_errors(
        self,
        operation: Optional[str] = None,
        error_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get filtered errors.
        
        Args:
            operation: Filter by operation
            error_type: Filter by error type
            limit: Maximum number of errors to return
            
        Returns:
            List of matching errors
        """
        filtered = self.errors
        
        if operation:
            filtered = [e for e in filtered if e['operation'] == operation]
            
        if error_type:
            filtered = [e for e in filtered if e['error_type'] == error_type]
            
        if limit:
            filtered = filtered[-limit:]
            
        return filtered
    
    def clear_errors(self) -> None:
        """Clear all tracked errors."""
        self.errors.clear()

def async_retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    logger: Optional[logging.Logger] = None
) -> Callable:
    """Decorator for async retry logic.
    
    Args:
        max_retries: Maximum number of retries
        delay: Initial delay between retries
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch
        logger: Optional logger instance
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        if logger:
                            logger.warning(
                                platform="retry",
                                status="retrying",
                                message=f"Attempt {attempt + 1} failed, retrying in {current_delay}s",
                                tags=["retry", "warning"]
                            )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        if logger:
                            logger.error(
                                platform="retry",
                                status="failed",
                                message=f"All {max_retries} attempts failed",
                                tags=["retry", "error"]
                            )
                        raise last_exception
            
            raise last_exception  # This should never be reached
            
        return wrapper
    return decorator

def track_operation(
    operation: str,
    logger: Optional[logging.Logger] = None,
    error_tracker: Optional[ErrorTracker] = None
) -> Callable:
    """Decorator to track operation execution.
    
    Args:
        operation: Operation name
        logger: Optional logger instance
        error_tracker: Optional error tracker
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            start_time = time.time()
            
            if logger:
                logger.info(
                    platform="operation",
                    status="started",
                    message=f"Starting {operation}",
                    tags=["operation", "start"]
                )
            
            try:
                result = await func(*args, **kwargs)
                
                duration = time.time() - start_time
                if logger:
                    logger.info(
                        platform="operation",
                        status="completed",
                        message=f"Completed {operation} in {duration:.2f}s",
                        tags=["operation", "success"]
                    )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                if error_tracker:
                    error_tracker.add_error(e, operation)
                
                if logger:
                    logger.error(
                        platform="operation",
                        status="failed",
                        message=f"{operation} failed after {duration:.2f}s: {str(e)}",
                        tags=["operation", "error"]
                    )
                
                raise
        
        return wrapper
    return decorator

def ensure_dir(path: Union[str, Path]) -> None:
    """Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Path to the directory
    """
    os.makedirs(path, exist_ok=True)

def atomic_write(filepath: str, content: str, mode: str = 'w') -> None:
    """
    Write content to file atomically.
    
    Args:
        filepath: Path to write to
        content: Content to write
        mode: File open mode
    """
    path = Path(filepath)
    temp = tempfile.NamedTemporaryFile(mode=mode, delete=False, dir=path.parent)
    try:
        temp.write(content)
        temp.close()
        os.replace(temp.name, path)
    except Exception:
        os.unlink(temp.name)
        raise

def safe_read(path: str | Path, mode: str = "r", encoding: str = "utf-8") -> str:
    """Safely read a file's contents.
    
    Args:
        path: Path to file
        mode: File open mode
        encoding: File encoding
        
    Returns:
        File contents or empty string if file doesn't exist
    """
    path = Path(path)
    if not path.exists():
        return ""
    with open(path, mode=mode, encoding=encoding) as f:
        return f.read()

def safe_write(path: str | Path, content: str, mode: str = "w", encoding: str = "utf-8") -> None:
    """Safely write content to a file.
    
    Args:
        path: Path to write to
        content: Content to write
        mode: File open mode
        encoding: File encoding
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, mode=mode, encoding=encoding) as f:
        f.write(content)

def load_json(file_path: str) -> dict:
    """Load JSON data from a file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        dict: The loaded JSON data
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in {file_path}: {str(e)}", e.doc, e.pos)

def save_json(file_path: str, data: dict, indent: int = 4) -> None:
    """Save data to a JSON file.
    
    Args:
        file_path: Path to save the JSON file
        data: Data to save
        indent: Number of spaces for indentation
        
    Raises:
        OSError: If the file cannot be written
        TypeError: If the data cannot be serialized to JSON
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent)
    except (OSError, TypeError) as e:
        raise type(e)(f"Failed to save JSON to {file_path}: {str(e)}")

def read_json(file_path: str) -> dict:
    """Alias for load_json for backward compatibility."""
    return load_json(file_path)

def backup_file(file_path: str, backup_dir: str = None) -> str:
    """Create a backup of a file.
    
    Args:
        file_path: Path to the file to backup
        backup_dir: Optional directory to store the backup. If None, creates
                   a backup in the same directory as the original file.
                   
    Returns:
        str: Path to the backup file
        
    Raises:
        FileNotFoundError: If the source file doesn't exist
        OSError: If the backup operation fails
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Source file not found: {file_path}")
        
    if backup_dir is None:
        backup_dir = os.path.dirname(file_path)
        
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.basename(file_path)
    backup_path = os.path.join(backup_dir, f"{filename}.{timestamp}.bak")
    
    shutil.copy2(file_path, backup_path)
    return backup_path

def transform_coordinates(x: int, y: int, scale: float = 1.0) -> Tuple[int, int]:
    """Transform screen coordinates.
    
    Args:
        x: X coordinate
        y: Y coordinate
        scale: Scale factor
        
    Returns:
        Transformed (x, y) coordinates
    """
    return (int(x * scale), int(y * scale))

def ensure_dir(directory: Union[str, Path]) -> None:
    """Ensure a directory exists.
    
    Args:
        directory: Directory path
    """
    Path(directory).mkdir(parents=True, exist_ok=True)

# Alias for ensure_dir
ensure_directory_exists = ensure_dir

def write_json(data: Dict[str, Any], path: Union[str, Path], indent: int = 2) -> None:
    """Write data to a JSON file.
    
    Args:
        data: The data to write
        path: Path to write to
        indent: JSON indentation level
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent)

def read_yaml(path: Union[str, Path]) -> Dict[str, Any]:
    """Read YAML file.
    
    Args:
        path: Path to YAML file
        
    Returns:
        Parsed YAML data
    """
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def write_yaml(data: Dict[str, Any], path: Union[str, Path], indent: int = 2) -> None:
    """Write data to YAML file.
    
    Args:
        data: Data to write
        path: Path to write to
        indent: Indentation level
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, indent=indent, sort_keys=False)

def load_yaml(path: str | Path) -> Dict[str, Any]:
    """Load data from a YAML file.
    
    Args:
        path: Path to read from
        
    Returns:
        The loaded data
    """
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

__all__ = [
    "ErrorTracker",
    "async_retry",
    "track_operation",
    "ensure_dir",
    "atomic_write",
    "safe_read",
    "safe_write",
    "load_json",
    "save_json",
    "read_json",
    "backup_file",
    "transform_coordinates",
    "write_json",
    "read_yaml",
    "write_yaml",
    "load_yaml"
] 