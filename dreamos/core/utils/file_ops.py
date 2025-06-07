"""File operation helpers extracted from file_utils."""

from __future__ import annotations

import logging
import os
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Union

from .safe_io import async_delete_file

logger = logging.getLogger(__name__)


def ensure_dir(path: Union[str, Path]) -> bool:
    """Ensure directory exists."""
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:  # pragma: no cover - simple log
        logger.error(f"Error creating directory {path}: {e}")
        return False


def clear_dir(path: Union[str, Path]) -> bool:
    """Clear directory contents."""
    try:
        for item in Path(path).glob("*"):
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        return True
    except Exception as e:  # pragma: no cover - simple log
        logger.error(f"Error clearing directory {path}: {e}")
        return False


def archive_file(
    file_path: Path, archive_dir: Path, logger: Optional[logging.Logger] = None
) -> bool:
    """Archive a file to the specified directory."""
    try:
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive_path = archive_dir / file_path.name
        file_path.rename(archive_path)
        if logger:
            logger.info(
                platform="file_ops",
                status="archived",
                message=f"Archived file {file_path.name}",
                tags=["archive", "success"],
            )
        return True
    except Exception as e:  # pragma: no cover - simple log
        if logger:
            logger.error(
                platform="file_ops",
                status="error",
                message=f"Error archiving file {file_path}: {e}",
                tags=["archive", "error"],
            )
        return False


def extract_agent_id(file_path: Path) -> Optional[str]:
    """Extract agent ID from a response file."""
    try:
        with open(file_path, "r") as f:
            response = json.load(f)
        return response.get("agent_id")
    except Exception as e:  # pragma: no cover - simple log
        logger.error(f"Error extracting agent ID from {file_path}: {e}")
        return None


def backup_file(
    file_path: Union[str, Path],
    backup_dir: Union[str, Path],
    logger: Optional[logging.Logger] = None,
) -> bool:
    """Create a backup of a file."""
    try:
        backup_dir = Path(backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / f"{Path(file_path).name}.bak"
        shutil.copy2(file_path, backup_path)
        if logger:
            logger.info(
                platform="file_ops",
                status="backed_up",
                message=f"Backed up file {file_path}",
                tags=["backup", "success"],
            )
        return True
    except Exception as e:  # pragma: no cover - simple log
        if logger:
            logger.error(
                platform="file_ops",
                status="error",
                message=f"Error backing up file {file_path}: {e}",
                tags=["backup", "error"],
            )
        return False


def safe_rmdir(path: Union[str, Path]) -> bool:
    """Safely remove a directory and its contents."""
    try:
        if os.path.exists(path):
            shutil.rmtree(path)
        return True
    except Exception as e:  # pragma: no cover - simple log
        logger.error(f"Error removing directory {path}: {e}")
        return False


async def cleanup_old_files(
    directory: Union[str, Path],
    max_age_hours: int = 24,
    pattern: str = "*.*",
    logger: Optional[logging.Logger] = None,
) -> List[Path]:
    """Clean up old files in a directory."""
    try:
        dir_path = Path(directory)
        now = datetime.now()
        deleted_files = []
        for filepath in dir_path.glob(pattern):
            age = now - datetime.fromtimestamp(filepath.stat().st_mtime)
            age_hours = age.total_seconds() / 3600
            if age_hours > max_age_hours:
                if await async_delete_file(filepath, logger):
                    deleted_files.append(filepath)
        if logger:
            logger.info(
                platform="file_ops",
                status="cleanup",
                message=f"Cleaned up {len(deleted_files)} old files",
                tags=["cleanup", "success"],
            )
        return deleted_files
    except Exception as e:  # pragma: no cover - simple log
        if logger:
            logger.error(
                platform="file_ops",
                status="error",
                message=f"Error cleaning up old files: {e}",
                tags=["cleanup", "error"],
            )
        return []
