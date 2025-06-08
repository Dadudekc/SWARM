"""Serialization helpers extracted from file_utils."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional, Union

import aiofiles
import yaml

from .safe_io import async_atomic_write, atomic_write
from .exceptions import FileOpsError, FileOpsIOError, FileOpsPermissionError

logger = logging.getLogger(__name__)

# Re-export stubs for backward compatibility
from .json_utils import (
    load_json as load_json,  # noqa
    save_json as save_json,  # noqa
    read_json as read_json,  # noqa
    write_json as write_json,  # noqa
    async_save_json as async_save_json,  # noqa
    async_load_json as async_load_json,  # noqa
)

from .yaml_utils import (
    load_yaml as load_yaml,  # noqa
    save_yaml as save_yaml,  # noqa
    read_yaml as read_yaml,  # noqa
    write_yaml as write_yaml,  # noqa
)

__all__ = [
    "load_json",
    "save_json",
    "read_json",
    "write_json",
    "async_save_json",
    "async_load_json",
    "load_yaml",
    "save_yaml",
    "read_yaml",
    "write_yaml",
]


def load_json(file_path: Union[str, Path], default: Any = None) -> Any:
    """Load JSON data from file."""
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            logger.info(
                "json_loaded",
                extra={
                    "path": str(file_path),
                    "size": len(str(data))
                }
            )
            return data
    except (json.JSONDecodeError, OSError, IOError) as e:
        logger.error(
            "json_load_error",
            extra={
                "path": str(file_path),
                "error": str(e)
            }
        )
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


def write_json(path: Union[str, Path], data: dict) -> None:
    """Write JSON to a file atomically."""
    path = Path(path)
    try:
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to JSON string
        content = json.dumps(data, indent=2)
        
        # Write atomically
        if not atomic_write(path, content):
            raise FileOpsIOError(f"Failed to write JSON to {path}")
            
        logger.info(
            "json_written",
            extra={
                "path": str(path),
                "size": len(content)
            }
        )
            
    except PermissionError as e:
        raise FileOpsPermissionError(f"Permission denied: {path}") from e
    except (OSError, IOError) as e:
        raise FileOpsIOError(f"I/O error: {path}") from e
    except TypeError as e:
        raise FileOpsError(f"JSON data cannot be serialized: {path}") from e


def restore_backup(backup_path: str, target_path: str) -> bool:
    """Restore a file from its backup."""
    try:
        if not Path(backup_path).exists():
            logger.error(f"Backup file not found: {backup_path}")
            return False
        Path(target_path).write_bytes(Path(backup_path).read_bytes())
        logger.info(f"Restored backup from {backup_path} to {target_path}")
        return True
    except Exception as e:  # pragma: no cover - simple log
        logger.error(f"Failed to restore backup from {backup_path}: {e}")
        return False


def read_yaml(path: Union[str, Path], default: Any = None) -> Any:
    """Read YAML from a file."""
    try:
        with open(path, 'r') as f:
            content = f.read()
            try:
                data = yaml.safe_load(content)
                logger.info(
                    "yaml_loaded",
                    extra={
                        "path": str(path),
                        "size": len(content)
                    }
                )
                return data
            except yaml.YAMLError as e:
                if default is not None:
                    return default
                raise FileOpsError(f'Invalid YAML in {path}: {e}')
    except (OSError, IOError) as e:
        if default is not None:
            return default
        raise FileOpsIOError(f'I/O error reading {path}') from e


def load_yaml(file_path: Union[str, Path], default: Any = None) -> Any:
    """Alias for read_yaml for backward compatibility."""
    return read_yaml(file_path, default)


def write_yaml(path: Union[str, Path], data: dict) -> None:
    """Write YAML to a file atomically."""
    try:
        # Convert to YAML string
        content = yaml.safe_dump(data, default_flow_style=False)
        
        # Write atomically
        if not atomic_write(path, content):
            raise FileOpsIOError(f"Failed to write YAML to {path}")
            
        logger.info(
            "yaml_written",
            extra={
                "path": str(path),
                "size": len(content)
            }
        )
            
    except PermissionError as e:
        raise FileOpsPermissionError(f'Permission denied: {path}') from e
    except (OSError, IOError) as e:
        raise FileOpsIOError(f'I/O error: {path}') from e
    except TypeError as e:
        raise FileOpsError(f'YAML data cannot be serialized: {path}') from e


def save_yaml(file_path: Union[str, Path], data: Any) -> bool:
    """Save data to YAML file."""
    return write_yaml(file_path, data)


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
