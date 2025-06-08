"""JSON serialization and deserialization utilities."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional, Union, Dict, List, Type

import aiofiles
from jsonschema import validate, ValidationError as SchemaValidationError

from .exceptions import DreamOSError
from .safe_io import async_atomic_write

logger = logging.getLogger(__name__)

__all__ = [
    "load_json",
    "save_json",
    "read_json",
    "write_json",
    "async_save_json",
    "async_load_json",
    "validate_json",
    "JsonValidationError"
]

class JsonValidationError(DreamOSError):
    """Raised when JSON validation fails."""
    def __init__(self, message: str, errors: Optional[List[str]] = None):
        super().__init__(message)
        self.errors = errors or []

def validate_json(data: Any, schema: Dict[str, Any]) -> None:
    """
    Validate JSON data against a schema.
    
    Args:
        data: The JSON data to validate
        schema: The JSON schema to validate against
        
    Raises:
        JsonValidationError: If validation fails
    """
    try:
        validate(instance=data, schema=schema)
    except SchemaValidationError as e:
        errors = [str(err) for err in e.context] if e.context else [str(e)]
        raise JsonValidationError(
            f"JSON validation failed: {e.message}",
            errors=errors
        )

def load_json(file_path: Union[str, Path], default: Any = None) -> Any:
    """Load JSON data from file."""
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:  # pragma: no cover - simple log
        logger.error(f"Error loading JSON from {file_path}: {e}")
        return default


def save_json(file_path: Union[str, Path], data: Any) -> bool:
    """Save data to JSON file."""
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:  # pragma: no cover - simple log
        logger.error(f"Error saving JSON to {file_path}: {e}")
        return False


def read_json(file_path: Union[str, Path], default: Any = None) -> Any:
    """Alias for load_json for backward compatibility."""
    return load_json(file_path, default)


def write_json(data: Any, filepath: str, indent: int = 4) -> bool:
    """Write data to a JSON file."""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent)
        return True
    except Exception as e:  # pragma: no cover - simple log
        logger.error(f"Failed to write JSON to {filepath}: {e}")
        return False


async def async_save_json(
    file_path: Union[str, Path],
    data: Any,
    logger: Optional[logging.Logger] = None,
) -> bool:
    """Save data to JSON file using async I/O."""
    try:
        content = json.dumps(data, indent=2)
        success = await async_atomic_write(file_path, content)
        if success and logger:
            logger.info(
                platform="file_ops",
                status="saved",
                message=f"Saved JSON to {Path(file_path).name}",
                tags=["json", "success"],
            )
        return success
    except Exception as e:  # pragma: no cover - simple log
        if logger:
            logger.error(
                platform="file_ops",
                status="error",
                message=f"Error saving JSON to {file_path}: {e}",
                tags=["json", "error"],
            )
        return False


async def async_load_json(
    file_path: Union[str, Path],
    default: Any = None,
    logger: Optional[logging.Logger] = None,
) -> Any:
    """Load JSON data from file using async I/O."""
    try:
        async with aiofiles.open(file_path, "r") as f:
            content = await f.read()
            return json.loads(content)
    except Exception as e:  # pragma: no cover - simple log
        if logger:
            logger.error(
                platform="file_ops",
                status="error",
                message=f"Error loading JSON from {file_path}: {e}",
                tags=["json", "error"],
            )
        return default 
