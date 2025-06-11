"""Unified file operations module with atomic operations and error recovery."""

from __future__ import annotations

import logging
import os
import shutil
import json
import asyncio
import aiofiles
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Union, Dict
from fasteners import InterProcessLock

from .safe_io import async_delete_file, atomic_write
from .exceptions import FileOpsError, FileOpsPermissionError, FileOpsIOError
from .metrics_utils import Counter

logger = logging.getLogger(__name__)

# Metrics
file_write_counter = Counter(
    "file_ops_write_total",
    "Total file writes",
    ["path", "operation"]
)

file_read_counter = Counter(
    "file_ops_read_total",
    "Total file reads",
    ["path", "operation"]
)

# Lock for directory operations
_dir_lock = InterProcessLock("dreamos_dir_ops")

class AtomicFileManager:
    """Manages atomic file operations with backup support and metrics."""
    
    def __init__(self, file_path: Union[str, Path], max_retries: int = 3):
        """Initialize the atomic file manager.
        
        Args:
            file_path: Path to the managed file
            max_retries: Maximum number of retry attempts for failed operations
        """
        self.file_path = Path(file_path)
        self._lock = asyncio.Lock()
        self._backup_path = self.file_path.with_suffix('.json.bak')
        self._temp_path = self.file_path.with_suffix('.json.tmp')
        self.max_retries = max_retries
        
        # Ensure directory exists
        ensure_dir(self.file_path.parent)
        
    async def atomic_write(self, data: Dict[str, Any]) -> bool:
        """Write data to file atomically with backup support.
        
        Args:
            data: Dictionary to write to file
            
        Returns:
            bool: True if write was successful
        """
        async with self._lock:
            for attempt in range(self.max_retries):
                try:
                    # Write to temp file first
                    async with aiofiles.open(self._temp_path, 'w', encoding='utf-8') as f:
                        await f.write(json.dumps(data, indent=2, default=str))
                    
                    # Backup current file if it exists
                    if self.file_path.exists():
                        os.replace(self.file_path, self._backup_path)
                    
                    # Atomic move of temp file to target
                    os.replace(self._temp_path, self.file_path)
                    
                    # Log metrics
                    file_write_counter.labels(
                        path=str(self.file_path),
                        operation="atomic_write"
                    ).inc()
                    
                    logger.info(
                        "file_write",
                        extra={
                            "path": str(self.file_path),
                            "bytes": len(json.dumps(data)),
                            "encoding": "utf-8"
                        }
                    )
                    return True
                    
                except Exception as e:
                    logger.error(
                        "file_write_error",
                        extra={
                            "path": str(self.file_path),
                            "error": str(e)
                        }
                    )
                    if attempt == self.max_retries - 1:
                        await self._handle_write_failure(e)
                        return False
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    
    async def atomic_read(self) -> Optional[Dict[str, Any]]:
        """Read data from file with backup recovery.
        
        Returns:
            Optional[Dict]: File contents or None if read fails
        """
        async with self._lock:
            try:
                async with aiofiles.open(self.file_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    
                    # Log metrics
                    file_read_counter.labels(
                        path=str(self.file_path),
                        operation="atomic_read"
                    ).inc()
                    
                    logger.info(
                        "file_read",
                        extra={
                            "path": str(self.file_path),
                            "bytes": len(content),
                            "encoding": "utf-8"
                        }
                    )
                    
                    return json.loads(content)
            except FileNotFoundError:
                logger.warning(f"File {self.file_path} not found")
                return None
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in {self.file_path}")
                return await self._recover_from_backup()
            except Exception as e:
                logger.error(
                    "file_read_error",
                    extra={
                        "path": str(self.file_path),
                        "error": str(e)
                    }
                )
                return await self._recover_from_backup()
                
    async def _recover_from_backup(self) -> Optional[Dict[str, Any]]:
        """Attempt to recover data from backup file.
        
        Returns:
            Optional[Dict]: Recovered data or None if recovery fails
        """
        if not self._backup_path.exists():
            logger.error("No backup file available for recovery")
            return None
            
        try:
            async with aiofiles.open(self._backup_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                data = json.loads(content)
                
            # Restore backup to main file
            os.replace(self._backup_path, self.file_path)
            logger.info(f"Recovered data from backup {self._backup_path}")
            return data
            
        except Exception as e:
            logger.error(f"Backup recovery failed: {str(e)}")
            return None
            
    async def _handle_write_failure(self, error: Exception):
        """Handle write operation failure.
        
        Args:
            error: The exception that caused the failure
        """
        logger.error(f"All write attempts failed: {str(error)}")
        
        # Attempt to restore from backup if available
        if self._backup_path.exists():
            try:
                os.replace(self._backup_path, self.file_path)
                logger.info("Restored from backup after write failure")
            except Exception as e:
                logger.error(f"Failed to restore from backup: {str(e)}")
                
    async def validate_file(self) -> bool:
        """Validate the file's JSON structure.
        
        Returns:
            bool: True if file is valid
        """
        try:
            data = await self.atomic_read()
            if data is None:
                return False
            # Basic structure validation
            return isinstance(data, dict)
        except Exception:
            return False
            
    async def cleanup(self):
        """Clean up temporary files."""
        try:
            if self._temp_path.exists():
                os.remove(self._temp_path)
        except Exception as e:
            logger.error(f"Failed to cleanup temp file: {str(e)}")

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
    backup_dir: Optional[Union[str, Path]] = None,
    move_to: Optional[Union[str, Path]] = None,
    logger: Optional[logging.Logger] = None,
    atomic: bool = True
) -> bool:
    """Create a backup of a file and optionally move it.
    
    Args:
        file_path: Path to the file to backup
        backup_dir: Directory to store backup (defaults to same directory as file)
        move_to: Optional destination to move file after backup
        logger: Optional logger instance
        atomic: Whether to use atomic operations for file moves
        
    Returns:
        bool: True if operation was successful
        
    Raises:
        FileNotFoundError: If source file doesn't exist
        FileOpsError: If operation fails
    """
    try:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Source file not found: {file_path}")
            
        # Determine backup location
        if backup_dir is None:
            backup_dir = file_path.parent
        else:
            backup_dir = Path(backup_dir)
            backup_dir.mkdir(parents=True, exist_ok=True)
            
        backup_path = backup_dir / f"{file_path.name}.bak"
        
        # Create backup using atomic operations if requested
        if atomic:
            with open(file_path, 'rb') as f:
                content = f.read()
            success = atomic_write(backup_path, content, mode='wb', encoding=None)
            if not success:
                raise FileOpsError(f"Failed to create atomic backup at {backup_path}")
        else:
            shutil.copy2(file_path, backup_path)
        
        # Move file if requested
        if move_to is not None:
            move_to = Path(move_to)
            move_to.parent.mkdir(parents=True, exist_ok=True)
            
            if atomic:
                with open(file_path, 'rb') as f:
                    content = f.read()
                success = atomic_write(move_to, content, mode='wb', encoding=None)
                if success:
                    os.remove(file_path)  # Remove original after successful atomic write
                else:
                    raise FileOpsError(f"Failed to move file atomically to {move_to}")
            else:
                shutil.move(file_path, move_to)
            
        if logger:
            logger.info(
                platform="file_ops",
                status="backed_up",
                message=f"Backed up file {file_path}",
                tags=["backup", "success"],
            )
        return True
        
    except Exception as e:
        if logger:
            logger.error(
                platform="file_ops",
                status="error",
                message=f"Error backing up file {file_path}: {e}",
                tags=["backup", "error"],
            )
        raise FileOpsError(f"File operation failed: {str(e)}") from e


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

def read_json(path: str | Path) -> Any:
    path = Path(path)
    if not path.exists():
        logger.warning(f"read_json: file not found: {path}")
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def write_json(path: str | Path, data: Any, atomic: bool = True) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if atomic:
        tmp_path = path.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        tmp_path.replace(path)
    else:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

def read_text(path: str | Path) -> Optional[str]:
    try:
        with Path(path).open("r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"read_text error: {e}")
        return None

def write_text(path: str | Path, text: str, atomic: bool = True) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if atomic:
        tmp_path = path.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as f:
            f.write(text)
        tmp_path.replace(path)
    else:
        with path.open("w", encoding="utf-8") as f:
            f.write(text)

def copy_file(src: str | Path, dest: str | Path) -> None:
    shutil.copy2(str(src), str(dest))
    logger.info(f"Copied {src} → {dest}")

def safe_delete(path: str | Path) -> None:
    try:
        Path(path).unlink()
        logger.info(f"Deleted file: {path}")
    except FileNotFoundError:
        logger.debug(f"File not found: {path}")
    except Exception as e:
        logger.warning(f"Failed to delete file {path}: {e}")
