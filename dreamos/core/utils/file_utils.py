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

logger = logging.getLogger(__name__)

def read_json(filepath: Union[str, Path]) -> Dict[str, Any]:
    """Read JSON data from a file.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        Dict containing the JSON data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
    """
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"JSON file not found: {filepath}")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in file {filepath}", e.doc, e.pos)

# Alias for backward compatibility
load_json = read_json

def write_json(data: Dict[str, Any], filepath: Union[str, Path]) -> None:
    """Write JSON data to a file.
    
    Args:
        data: Dict to write as JSON
        filepath: Path to write the JSON file to
        
    Raises:
        OSError: If file cannot be written
        TypeError: If data cannot be serialized to JSON
    """
    try:
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    except (OSError, IOError) as e:
        raise OSError(f"Failed to write JSON file {filepath}: {str(e)}")
    except TypeError as e:
        raise TypeError(f"Data cannot be serialized to JSON: {str(e)}")

# Alias for backward compatibility
save_json = write_json

def ensure_dir(path: Union[str, Path]) -> None:
    """Ensure a directory exists.
    
    Args:
        path: Path to the directory (string or Path object)
    """
    path = Path(path) if isinstance(path, str) else path
    path.mkdir(parents=True, exist_ok=True)
    
def safe_rmdir(path: Path, recursive: bool = False) -> None:
    """Safely remove a directory.
    
    Args:
        path: Path to the directory
        recursive: Whether to remove recursively
    """
    if recursive:
        shutil.rmtree(path, ignore_errors=True)
    else:
        try:
            os.rmdir(path)
        except OSError:
            pass

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

__all__ = [
    "atomic_write",
    "safe_read",
    "safe_write",
    "async_atomic_write",
    "async_delete_file",
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
    "YamlError"
]
