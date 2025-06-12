"""
Core Utilities
-------------
Core utility functions for the Dream.OS system.
"""

import json
import logging
import os
import shutil
import uuid
import functools
import asyncio
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar, Union
import time

from .file_ops import (
    backup_file,
    ensure_dir,
    safe_rmdir,
    FileOpsError
)
from .safe_io import (
    atomic_write,
    safe_read,
    safe_write,
    SafeIOError
)

logger = logging.getLogger(__name__)

# Type variable for generic functions
T = TypeVar('T')

# Track errors
_errors: List[str] = []

def add_error(error: str) -> None:
    """Add an error to the tracked errors list."""
    _errors.append(error)

class ErrorTracker:
    """Track errors with context."""
    
    def __init__(self, max_errors: int = 100):
        """Initialize error tracker.
        
        Args:
            max_errors: Maximum number of errors to track
        """
        self.max_errors = max_errors
        self.errors: List[Dict[str, Any]] = []
    
    def add_error(
        self,
        error: Exception,
        operation: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add an error with context.
        
        Args:
            error: Exception that occurred
            operation: Operation that failed
            context: Additional context about the error
        """
        error_info = {
            "error": str(error),
            "operation": operation,
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        }
        
        self.errors.append(error_info)
        if len(self.errors) > self.max_errors:
            self.errors.pop(0)
    
    def get_errors(
        self,
        operation: Optional[str] = None,
        error_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get tracked errors with optional filtering.
        
        Args:
            operation: Filter by operation name
            error_type: Filter by error type
            limit: Maximum number of errors to return
            
        Returns:
            List of error dictionaries
        """
        errors = self.errors
        
        if operation:
            errors = [e for e in errors if e["operation"] == operation]
            
        if error_type:
            errors = [e for e in errors if error_type in str(e["error"])]
            
        if limit:
            errors = errors[-limit:]
            
        return errors
    
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
    """Decorator for retrying async functions.
    
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
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        if logger:
                            logger.warning(
                                f"Retry {attempt + 1}/{max_retries} for {func.__name__} "
                                f"after {current_delay}s: {str(e)}"
                            )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        if logger:
                            logger.error(
                                f"All {max_retries} retries failed for {func.__name__}: {str(e)}"
                            )
                        raise last_exception
                        
            raise last_exception
            
        return wrapper
    return decorator

def with_retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    logger: Optional[logging.Logger] = None
) -> Callable:
    """Decorator for retrying synchronous functions.
    
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
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        if logger:
                            logger.warning(
                                f"Retry {attempt + 1}/{max_retries} for {func.__name__} "
                                f"after {current_delay}s: {str(e)}"
                            )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        if logger:
                            logger.error(
                                f"All {max_retries} retries failed for {func.__name__}: {str(e)}"
                            )
                        raise last_exception
                        
            raise last_exception
            
        return wrapper
    return decorator

def track_operation(
    operation: str,
    logger: Optional[logging.Logger] = None,
    error_tracker: Optional[ErrorTracker] = None
) -> Callable:
    """Decorator for tracking operations.
    
    Args:
        operation: Name of the operation
        logger: Optional logger instance
        error_tracker: Optional error tracker instance
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            start_time = datetime.now()
            
            try:
                result = await func(*args, **kwargs)
                
                if logger:
                    duration = (datetime.now() - start_time).total_seconds()
                    logger.info(
                        f"Operation {operation} completed in {duration:.2f}s",
                        extra={
                            "operation": operation,
                            "duration": duration,
                            "status": "success"
                        }
                    )
                    
                return result
                
            except Exception as e:
                if logger:
                    logger.error(
                        f"Operation {operation} failed: {str(e)}",
                        extra={
                            "operation": operation,
                            "error": str(e),
                            "status": "error"
                        }
                    )
                    
                if error_tracker:
                    error_tracker.add_error(e, operation)
                    
                raise
                
        return wrapper
    return decorator

def format_message(content: str, **kwargs: Any) -> str:
    """Format a message with the given content and keyword arguments.
    
    Args:
        content: Message content
        **kwargs: Additional message fields
        
    Returns:
        Formatted message string
    """
    message = {
        'content': content,
        'timestamp': datetime.now().isoformat(),
        **kwargs
    }
    return json.dumps(message)

def parse_message(message: str) -> Dict[str, Any]:
    """Parse a message string into a dictionary.
    
    Args:
        message: Message string to parse
        
    Returns:
        Parsed message dictionary
        
    Raises:
        ValueError: If message is invalid JSON
    """
    try:
        return json.loads(message)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid message format: {str(e)}")

def get_timestamp() -> float:
    """Get current timestamp in seconds."""
    return time.time()

def format_duration(seconds: float) -> str:
    """Format duration in seconds to a string."""
    return f"{seconds:.2f}s"

def is_valid_uuid(val: Any) -> bool:
    """Check if value is a valid UUID string."""
    try:
        uuid.UUID(str(val))
        return True
    except Exception:
        return False

def get_errors() -> List[str]:
    """Get list of tracked errors."""
    return _errors.copy()

def clear_errors() -> None:
    """Clear all tracked errors."""
    _errors.clear()

def decorator(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator function for core utilities."""
    def wrapped(*args: Any, **kwargs: Any) -> T:
        return func(*args, **kwargs)
    return wrapped

def safe_move(src_path: str, dst_path: str, backup: bool = True, atomic: bool = True) -> bool:
    """Safely move a file with optional backup.
    
    Args:
        src_path: Source file path
        dst_path: Destination file path
        backup: Whether to create a backup before moving
        atomic: Whether to use atomic operations for the move
        
    Returns:
        bool: True if move was successful, False otherwise
        
    Raises:
        FileNotFoundError: If the source file doesn't exist
        FileOpsError: If the move operation fails
    """
    try:
        if backup:
            # Use enhanced backup_file with move capability
            return backup_file(
                file_path=src_path,
                move_to=dst_path,
                logger=logger,
                atomic=atomic
            )
        else:
            # Just move without backup
            if atomic:
                with open(src_path, 'rb') as f:
                    content = f.read()
                success = atomic_write(dst_path, content, mode='wb', encoding=None)
                if success:
                    os.remove(src_path)  # Remove original after successful atomic write
                    return True
                else:
                    raise FileOpsError(f"Failed to move file atomically to {dst_path}")
            else:
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                shutil.move(src_path, dst_path)
                return True
            
    except Exception as e:
        logger.error(f"Error moving {src_path} to {dst_path}: {e}")
        raise FileOpsError(f"Move operation failed: {str(e)}") from e


def format_timestamp(timestamp: Optional[Union[str, float, datetime]] = None) -> str:
    """Format a timestamp consistently.
    Args:
        timestamp: Optional timestamp to format. If None, uses current time.
        Accepts float (epoch), str (iso), or datetime.
    Returns:
        Formatted timestamp string in ISO format
    """
    if timestamp is None:
        timestamp = datetime.now()
    elif isinstance(timestamp, float):
        timestamp = datetime.fromtimestamp(timestamp)
    elif isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp)
        except ValueError:
            try:
                timestamp = datetime.fromtimestamp(float(timestamp))
            except Exception:
                timestamp = datetime.now()
    return timestamp.isoformat()

def generate_id() -> str:
    """Generate a unique identifier."""
    return str(uuid.uuid4())

def read_yaml(path: Union[str, Path]) -> Dict[str, Any]:
    """Reads a YAML file and returns the contents as a dictionary.
    
    Args:
        path: Path to the YAML file
        
    Returns:
        Dict containing the YAML contents
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        yaml.YAMLError: If the YAML is invalid
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {path}")
        
    try:
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file {path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error reading YAML file {path}: {e}")
        raise

def write_yaml(data: Dict[str, Any], path: Union[str, Path]) -> None:
    """Write data to a YAML file.
    
    Args:
        data: Dictionary to write
        path: Path to write to
        
    Raises:
        FileNotFoundError: If parent directory doesn't exist
        yaml.YAMLError: If data can't be serialized to YAML
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, default_flow_style=False)
    except yaml.YAMLError as e:
        logger.error(f"Error writing YAML to {path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error writing to {path}: {e}")
        raise

def atomic_write(data: Any, path: Union[str, Path]) -> None:
    """Write data to file atomically.
    
    Args:
        data: Data to write
        path: Path to write to
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    temp_path = path.with_suffix('.tmp')
    try:
        with temp_path.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        os.replace(temp_path, path)
    except Exception as e:
        logger.error(f"Error writing to {path}: {e}")
        if temp_path.exists():
            temp_path.unlink()
        raise


def load_json(path: Union[str, Path], default: Any = None) -> Any:
    """Load JSON data from file.
    
    Args:
        path: Path to read from
        default: Default value if file doesn't exist
        
    Returns:
        Loaded JSON data or default
    """
    path = Path(path)
    if not path.exists():
        return default
        
    try:
        with path.open('r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON from {path}: {e}")
        return default

def save_json(data: Any, path: Union[str, Path], pretty: bool = True) -> None:
    """Save data as JSON.
    
    Args:
        data: Data to save
        path: Path to save to
        pretty: Whether to pretty-print
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with path.open('w', encoding='utf-8') as f:
            if pretty:
                json.dump(data, f, indent=2)
            else:
                json.dump(data, f)
    except Exception as e:
        logger.error(f"Error saving JSON to {path}: {e}")
        raise

def read_json(path: Union[str, Path], default: Any = None) -> Any:
    """Alias for load_json."""
    return load_json(path, default)

def write_json(data: Any, path: Union[str, Path], pretty: bool = True) -> None:
    """Alias for save_json."""
    return save_json(data, path, pretty)

def ensure_directory_exists(path: Union[str, Path]) -> None:
    """Alias for ensure_dir."""
    return ensure_dir(path)

def load_yaml(path: Union[str, Path], default: Any = None) -> Any:
    """Alias for read_yaml."""
    return read_yaml(path)

def transform_coordinates(x: int, y: int, scale: float = 1.0, offset_x: int = 0, offset_y: int = 0) -> tuple[int, int]:
    """Transform coordinates with scaling and offset.
    
    Args:
        x: X coordinate
        y: Y coordinate
        scale: Scale factor
        offset_x: X offset
        offset_y: Y offset
        
    Returns:
        Tuple of (transformed_x, transformed_y)
    """
    return (
        int(x * scale + offset_x),
        int(y * scale + offset_y)
    )

__all__ = [
    "ErrorTracker",
    "add_error",
    "async_retry",
    "with_retry",
    "track_operation",
    "format_message",
    "parse_message",
    "get_timestamp",
    "format_duration",
    "is_valid_uuid",
    "get_errors",
    "clear_errors",
    "safe_move",
    "load_json",
    "save_json",
    "read_json",
    "write_json",
    "format_timestamp",
    "generate_id",
    "backup_file",
    "transform_coordinates",
    "read_yaml",
    "write_yaml",
    "load_yaml",
    "atomic_write",
    "safe_read",
    "safe_write",
    "ensure_directory_exists",
]
