"""Aggregate helpers for backward compatibility."""

import json
from pathlib import Path
from typing import Any, Optional, Union
import logging

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

logger = logging.getLogger(__name__)

def read_json(file_path: Union[str, Path], default: Any = None) -> Any:
    """Safely read and parse JSON from file.
    
    Args:
        file_path: Path to JSON file
        default: Value to return if read/parse fails
        
    Returns:
        Parsed JSON data or default value if read/parse fails
    """
    try:
        return _read_json(file_path)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(
            "json_parse_error",
            extra={
                "path": str(file_path),
                "error": str(e)
            }
        )
        return default

# Alias for backward compatibility
load_json = read_json

def write_json(data: Any, file_path: Union[str, Path], **kwargs) -> None:
    """Write data to JSON file.
    
    Args:
        data: Data to write
        file_path: Path to write to
        **kwargs: Additional arguments passed to _write_json
    """
    _write_json(data, file_path, **kwargs)

# Alias for backward compatibility
save_json = write_json

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
]
