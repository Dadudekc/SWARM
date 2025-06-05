"""
File Operations Module
--------------------
Centralized file operations for Dream.OS with cross-platform compatibility
and consistent error handling.
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class FileOpsError(Exception):
    """Base exception for file operations."""
    pass

class FileOpsPermissionError(FileOpsError):
    """Raised when file operations fail due to permissions."""
    pass

class FileOpsIOError(FileOpsError):
    """Raised when file operations fail due to I/O errors."""
    pass

@contextmanager
def safe_file_handle(path: Union[str, Path], mode: str = 'r', encoding: str = 'utf-8'):
    """Safely handle file operations with proper error handling.
    
    Args:
        path: File path
        mode: File open mode
        encoding: File encoding
        
    Yields:
        File handle
        
    Raises:
        FileOpsPermissionError: If permission denied
        FileOpsIOError: For other I/O errors
    """
    path = Path(path)
    try:
        with open(path, mode, encoding=encoding) as f:
            yield f
    except PermissionError as e:
        raise FileOpsPermissionError(f"Permission denied: {path}") from e
    except IOError as e:
        raise FileOpsIOError(f"I/O error with {path}: {str(e)}") from e

def ensure_dir(path: Union[str, Path], mode: int = 0o755) -> Path:
    """Ensure directory exists with proper permissions.
    
    Args:
        path: Directory path
        mode: Directory permissions (Unix only)
        
    Returns:
        Path: Created directory path
        
    Raises:
        FileOpsPermissionError: If permission denied
        FileOpsIOError: For other I/O errors
    """
    path = Path(path)
    try:
        path.mkdir(parents=True, exist_ok=True)
        if os.name != 'nt':  # Not Windows
            os.chmod(path, mode)
        return path
    except PermissionError as e:
        raise FileOpsPermissionError(f"Permission denied creating directory: {path}") from e
    except IOError as e:
        raise FileOpsIOError(f"I/O error creating directory {path}: {str(e)}") from e

def safe_rmdir(path: Union[str, Path], recursive: bool = False) -> None:
    """Safely remove directory.
    
    Args:
        path: Directory path
        recursive: Whether to remove recursively
        
    Raises:
        FileOpsPermissionError: If permission denied
        FileOpsIOError: For other I/O errors
    """
    path = Path(path)
    try:
        if recursive:
            import shutil
            shutil.rmtree(path)
        else:
            path.rmdir()
    except PermissionError as e:
        raise FileOpsPermissionError(f"Permission denied removing directory: {path}") from e
    except IOError as e:
        raise FileOpsIOError(f"I/O error removing directory {path}: {str(e)}") from e

def read_json(path: Union[str, Path], default: Any = None) -> Any:
    """Read JSON file with error handling.
    
    Args:
        path: JSON file path
        default: Default value if file doesn't exist
        
    Returns:
        Any: JSON data or default value
        
    Raises:
        FileOpsPermissionError: If permission denied
        FileOpsIOError: For other I/O errors
    """
    path = Path(path)
    if not path.exists():
        return default
        
    try:
        with safe_file_handle(path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {path}: {str(e)}")
        return default

def write_json(path: Union[str, Path], data: Any, indent: int = 4) -> None:
    """Write JSON file with error handling.
    
    Args:
        path: JSON file path
        data: Data to write
        indent: JSON indentation
        
    Raises:
        FileOpsPermissionError: If permission denied
        FileOpsIOError: For other I/O errors
    """
    path = Path(path)
    ensure_dir(path.parent)
    
    try:
        with safe_file_handle(path, 'w') as f:
            json.dump(data, f, indent=indent)
        if os.name != 'nt':  # Not Windows
            os.chmod(path, 0o600)  # User-only permissions
    except TypeError as e:
        raise FileOpsIOError(f"Invalid JSON data: {str(e)}") from e

def read_yaml(path: Union[str, Path], default: Any = None) -> Any:
    """Read YAML file with error handling.
    
    Args:
        path: YAML file path
        default: Default value if file doesn't exist
        
    Returns:
        Any: YAML data or default value
        
    Raises:
        FileOpsPermissionError: If permission denied
        FileOpsIOError: For other I/O errors
    """
    path = Path(path)
    if not path.exists():
        return default
        
    try:
        with safe_file_handle(path, 'r') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in {path}: {str(e)}")
        return default

def write_yaml(path: Union[str, Path], data: Any) -> None:
    """Write YAML file with error handling.
    
    Args:
        path: YAML file path
        data: Data to write
        
    Raises:
        FileOpsPermissionError: If permission denied
        FileOpsIOError: For other I/O errors
    """
    path = Path(path)
    ensure_dir(path.parent)
    
    try:
        with safe_file_handle(path, 'w') as f:
            yaml.safe_dump(data, f, default_flow_style=False)
        if os.name != 'nt':  # Not Windows
            os.chmod(path, 0o600)  # User-only permissions
    except yaml.YAMLError as e:
        raise FileOpsIOError(f"Invalid YAML data: {str(e)}") from e

def rotate_file(path: Union[str, Path], max_size: int = 10 * 1024 * 1024,  # 10MB
                max_files: int = 5) -> None:
    """Rotate file if it exceeds size limit.
    
    Args:
        path: File path
        max_size: Maximum file size in bytes
        max_files: Maximum number of backup files
        
    Raises:
        FileOpsPermissionError: If permission denied
        FileOpsIOError: For other I/O errors
    """
    path = Path(path)
    if not path.exists() or path.stat().st_size < max_size:
        return
        
    try:
        # Remove oldest backup if at limit
        oldest = path.with_suffix(f'.{max_files}')
        if oldest.exists():
            oldest.unlink()
            
        # Rotate existing backups
        for i in range(max_files - 1, 0, -1):
            old = path.with_suffix(f'.{i}')
            new = path.with_suffix(f'.{i + 1}')
            if old.exists():
                old.rename(new)
                
        # Rename current file
        path.rename(path.with_suffix('.1'))
    except PermissionError as e:
        raise FileOpsPermissionError(f"Permission denied rotating file: {path}") from e
    except IOError as e:
        raise FileOpsIOError(f"I/O error rotating file {path}: {str(e)}") from e 