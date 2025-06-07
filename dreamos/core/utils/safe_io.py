"""Safe file I/O helpers extracted from file_utils."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Optional, Union

import aiofiles

logger = logging.getLogger(__name__)


def atomic_write(file_path: Union[str, Path], content: str, mode: str = "w") -> bool:
    """Write content to file atomically."""
    try:
        temp_path = f"{file_path}.tmp"
        with open(temp_path, mode) as f:
            f.write(content)
        os.replace(temp_path, file_path)
        return True
    except Exception as e:  # pragma: no cover - simple log
        logger.error(f"Error in atomic write to {file_path}: {e}")
        return False


def safe_read(file_path: Union[str, Path], default: Any = None) -> Any:
    """Safely read content from file."""
    try:
        with open(file_path, "r") as f:
            return f.read()
    except Exception as e:  # pragma: no cover - simple log
        logger.error(f"Error reading {file_path}: {e}")
        return default


def safe_write(file_path: Union[str, Path], content: str) -> bool:
    """Safely write content to file."""
    try:
        with open(file_path, "w") as f:
            f.write(content)
        return True
    except Exception as e:  # pragma: no cover - simple log
        logger.error(f"Error writing to {file_path}: {e}")
        return False


async def async_atomic_write(
    file_path: Union[str, Path], content: str, mode: str = "w"
) -> bool:
    """Write content to file atomically using async I/O."""
    try:
        path = Path(file_path)
        temp_path = path.with_suffix(".tmp")
        async with aiofiles.open(temp_path, mode) as f:
            await f.write(content)
        os.replace(temp_path, path)
        return True
    except Exception as e:  # pragma: no cover - simple log
        logger.error(f"Error in async atomic write to {file_path}: {e}")
        if temp_path.exists():
            temp_path.unlink()
        return False


async def async_delete_file(
    file_path: Union[str, Path], logger: Optional[logging.Logger] = None
) -> bool:
    """Delete a file using async I/O."""
    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
            if logger:
                logger.info(
                    platform="file_ops",
                    status="deleted",
                    message=f"Deleted file {path.name}",
                    tags=["delete", "success"],
                )
            return True
        return False
    except Exception as e:  # pragma: no cover - simple log
        if logger:
            logger.error(
                platform="file_ops",
                status="error",
                message=f"Error deleting file {file_path}: {e}",
                tags=["delete", "error"],
            )
        return False
