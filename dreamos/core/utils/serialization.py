"""Serialization helpers extracted from file_utils."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional, Union

import aiofiles
import yaml

from .safe_io import async_atomic_write

logger = logging.getLogger(__name__)


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


def read_yaml(file_path: Union[str, Path], default: Any = None) -> Any:
    """Read YAML data from file."""
    try:
        with open(file_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:  # pragma: no cover - simple log
        logger.error(f"Error reading YAML from {file_path}: {e}")
        return default


def load_yaml(file_path: Union[str, Path], default: Any = None) -> Any:
    """Alias for read_yaml for backward compatibility."""
    return read_yaml(file_path, default)


def write_yaml(file_path: Union[str, Path], data: Any) -> bool:
    """Write data to YAML file."""
    try:
        with open(file_path, "w") as f:
            yaml.safe_dump(data, f, default_flow_style=False)
        return True
    except Exception as e:  # pragma: no cover - simple log
        logger.error(f"Error writing YAML to {file_path}: {e}")
        return False


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
