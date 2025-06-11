"""Aggregate helpers for backward compatibility."""

import json
from pathlib import Path
from typing import Any, Optional, Union, Dict, List
import logging
import os
import shutil

from .safe_io import (
    atomic_write,
    safe_read,
    safe_write,
    async_atomic_write,
    async_delete_file,
    safe_file_handle,
)

from .file_ops import (
    ensure_dir,
    clear_dir,
    archive_file,
    extract_agent_id,
    backup_file,
    safe_rmdir,
    cleanup_old_files,
)

from ..io.json_ops import read_json as _read_json, write_json as _write_json

from .yaml_utils import (
    read_yaml,
    write_yaml,
    load_yaml,
    save_yaml,
    YamlError
)

from dreamos.social.utils.log_rotator import LogRotator
from dreamos.core.utils.exceptions import FileOpsError, FileOpsPermissionError, FileOpsIOError

logger = logging.getLogger(__name__)

def read_json(filepath: Union[str, Path], default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Read JSON data from a file.
    
    Args:
        filepath: Path to the JSON file
        default: Default value to return if file doesn't exist or is invalid
        
    Returns:
        Dict containing the JSON data
        
    Raises:
        FileNotFoundError: If file doesn't exist and no default provided
        json.JSONDecodeError: If file contains invalid JSON and no default provided
    """
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        if default is not None:
            return default
        if isinstance(e, FileNotFoundError):
            raise FileNotFoundError(f"JSON file not found: {filepath}") from e
        raise json.JSONDecodeError(f"Invalid JSON in file {filepath}", e.doc, e.pos) from e

# Alias for backward compatibility
load_json = read_json

def write_json(data: Dict[str, Any], filepath: Union[str, Path]) -> None:
    """Write data to a JSON file.
    
    Args:
        data: Data to write
        filepath: Path to write to
        
    Raises:
        FileOpsError: If write fails or path is invalid
    """
    try:
        filepath = Path(filepath)
        # Validate path is not a Windows reserved device name
        if os.name == 'nt':  # Windows
            invalid_devices = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
                             'LPT1', 'LPT2', 'LPT3', 'LPT4']
            if any(filepath.name.upper().startswith(device) for device in invalid_devices):
                raise FileOpsError(f"Invalid path: {filepath} is a reserved Windows device name")
        
        # Only create directory if the path is not empty
        dirname = os.path.dirname(str(filepath))
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        raise FileOpsError(f"Failed to write JSON file {filepath}: {str(e)}") from e

# Alias for backward compatibility
save_json = write_json

def ensure_dir(path: Union[str, Path]) -> Path:
    """Ensure a directory exists with proper permissions.
    
    Args:
        path: Path to the directory (string or Path object)
        
    Returns:
        Path object for the created/existing directory
        
    Raises:
        FileOpsError: If path exists and is a file
        FileOpsPermissionError: If permission denied
        FileOpsIOError: If other I/O error occurs
    """
    path = Path(path) if isinstance(path, str) else path
    
    if path.exists() and path.is_file():
        raise FileOpsError(f"Path {path} exists and is a file")
        
    try:
        path.mkdir(parents=True, exist_ok=True)
        if os.name != 'nt':  # Unix-like systems
            os.chmod(path, 0o755)  # rwxr-xr-x
        return path
    except PermissionError as e:
        raise FileOpsPermissionError(f"Permission denied: {path}") from e
    except OSError as e:
        raise FileOpsIOError(f"I/O error: {path}") from e

def safe_rmdir(path: Union[str, Path], recursive: bool = False) -> None:
    """Safely remove a directory.
    
    Args:
        path: Path to the directory
        recursive: Whether to remove recursively
        
    Raises:
        FileOpsError: If path exists and is a file
        FileOpsPermissionError: If permission denied
        FileOpsIOError: If other I/O error occurs
    """
    path = Path(path) if isinstance(path, str) else path
    
    if path.exists() and path.is_file():
        raise FileOpsError(f"Path {path} exists and is a file")
        
    try:
        if recursive:
            shutil.rmtree(path)
        else:
            os.rmdir(path)
    except PermissionError as e:
        raise FileOpsPermissionError(f"Permission denied: {path}") from e
    except OSError as e:
        raise FileOpsIOError(f"I/O error: {path}") from e

# Alias for backward compatibility
clean_dir = clear_dir

def get_file_info(path):
    """Stub for get_file_info. Returns basic file info or empty dict."""
    return {}

class FileError(Exception):
    """Stub for FileError exception."""
    pass

async def async_save_json(data, filepath):
    """Asynchronously save data to a JSON file."""
    # TODO: Implement actual async JSON saving logic
    pass

def restore_backup(src: Path, backup_dir: Path) -> None:  # noqa: D401
    """
    Legacy helper — noop in modern Dream.OS but tests still import it.
    Simply copy *src* to *backup_dir/src.bak*.
    """
    backup_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, backup_dir / f"{src.name}.bak")

def find_files(directory: str, extension: str = '.py') -> List[Path]:
    """Find all files with given extension in directory.
    
    Args:
        directory: Directory to search in
        extension: File extension to match (default: .py)
        
    Returns:
        List of Path objects for matching files
    """
    return list(Path(directory).rglob(f'*{extension}'))

def rotate_file(filepath, log_dir=None, max_size=10 * 1024 * 1024, max_files=5, compress_after_days=7):
    """Rotate a file using LogRotator for backward compatibility.
    
    Args:
        filepath: Path to the file to rotate
        log_dir: Directory to store rotated files (defaults to file's directory)
        max_size: Maximum file size in bytes before rotation
        max_files: Maximum number of rotated files to keep
        compress_after_days: Days after which to compress rotated files
        
    Returns:
        Path to the rotated file
        
    Raises:
        FileOpsError: If rotation fails
    """
    try:
        if log_dir is None:
            log_dir = Path(filepath).parent
        filepath = Path(filepath)
        
        # Check if file needs rotation
        if not filepath.exists() or filepath.stat().st_size < max_size:
            return filepath
            
        # Rotate existing backup files
        for i in range(max_files - 1, 0, -1):
            old = filepath.with_suffix(f'.{i}')
            new = filepath.with_suffix(f'.{i + 1}')
            if old.exists():
                if new.exists():
                    new.unlink()
                old.rename(new)
                
        # Move current file to .1
        filepath.rename(filepath.with_suffix('.1'))
        
        # Create new empty file
        filepath.touch()
        
        # Delete the original file
        filepath.unlink()
        
        return filepath
    except Exception as e:
        raise FileOpsError(f"Failed to rotate file {filepath}: {e}") from e

__all__ = [
    "atomic_write",
    "safe_read",
    "safe_write",
    "async_atomic_write",
    "async_delete_file",
    "safe_file_handle",
    "ensure_dir",
    "clear_dir",
    "archive_file",
    "extract_agent_id",
    "backup_file",
    "safe_rmdir",
    "cleanup_old_files",
    "read_json",
    "write_json",
    "load_json",
    "save_json",
    "get_file_info",
    "FileError",
    "async_save_json",
    "restore_backup",
    "read_yaml",
    "write_yaml",
    "load_yaml",
    "save_yaml",
    "find_files",
    "YamlError",
    "rotate_file",
    "FileOpsError",
    "FileOpsPermissionError",
    "FileOpsIOError"
]
