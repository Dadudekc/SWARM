"""File operation helpers extracted from file_utils."""

from __future__ import annotations

import logging
import os
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Union
from fasteners import InterProcessLock

from .safe_io import async_delete_file, atomic_write
from .exceptions import FileOpsError, FileOpsPermissionError, FileOpsIOError

logger = logging.getLogger(__name__)

# Lock for directory operations
_dir_lock = InterProcessLock("dreamos_dir_ops")

def safe_mkdir(path: Union[str, Path]) -> None:
    """Safely create a directory with concurrency protection.
    
    Args:
        path: Path to create directory at
        
    Raises:
        FileOpsError: If path exists and is a file
        FileOpsPermissionError: If permission denied
        FileOpsIOError: If other I/O error occurs
    """
    path = Path(path)
    if path.exists() and path.is_file():
        raise FileOpsError(f"Path {path} exists and is a file")
        
    with _dir_lock:
        try:
            path.mkdir(parents=True, exist_ok=True)
            logger.info(
                "directory_created",
                extra={"path": str(path)}
            )
        except PermissionError as e:
            logger.error(
                "directory_create_permission_error",
                extra={
                    "path": str(path),
                    "error": str(e)
                }
            )
            raise FileOpsPermissionError(f"Permission denied: {path}") from e
        except OSError as e:
            logger.error(
                "directory_create_error",
                extra={
                    "path": str(path),
                    "error": str(e)
                }
            )
            raise FileOpsIOError(f"I/O error: {path}") from e


def ensure_dir(path: Union[str, Path]) -> bool:
    """Ensure directory exists with concurrency protection."""
    try:
        safe_mkdir(path)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {path}: {e}")
        return False


def clear_dir(path: Union[str, Path]) -> bool:
    """Clear directory contents safely."""
    path = Path(path)
    try:
        with _dir_lock:
            if path.exists():
                shutil.rmtree(path)
                path.mkdir(parents=True)
                logger.info(
                    "directory_cleared",
                    extra={"path": str(path)}
                )
        return True
    except Exception as e:
        logger.error(
            "directory_clear_error",
            extra={
                "path": str(path),
                "error": str(e)
            }
        )
        return False


def archive_file(
    source: Union[str, Path],
    dest: Union[str, Path],
    timestamp: Optional[datetime] = None
) -> bool:
    """Archive a file with atomic operations."""
    source = Path(source)
    dest = Path(dest)
    
    if not source.exists():
        return False
        
    try:
        # Ensure destination directory exists
        dest.parent.mkdir(parents=True, exist_ok=True)
        
        # Read source content
        with open(source, 'rb') as f:
            content = f.read()
            
        # Write to destination atomically
        success = atomic_write(
            dest,
            content,
            mode='wb',
            encoding=None  # Binary mode
        )
        
        if success:
            logger.info(
                "file_archived",
                extra={
                    "source": str(source),
                    "dest": str(dest)
                }
            )
            
        return success
        
    except Exception as e:
        logger.error(
            "file_archive_error",
            extra={
                "source": str(source),
                "dest": str(dest),
                "error": str(e)
            }
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
