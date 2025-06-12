"""Unified file operations module with atomic operations and error recovery."""

from __future__ import annotations

import os
import shutil
import json
import asyncio
import aiofiles
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Union, Dict, TypeVar, Generic, ContextManager
from contextlib import contextmanager
from fasteners import InterProcessLock

from .safe_io import async_delete_file, atomic_write
from .exceptions import FileOpsError, FileOpsPermissionError, FileOpsIOError, handle_error
from .metrics import metrics, logger, log_operation

# Type variables for generic file operations
T = TypeVar('T')
FileData = TypeVar('FileData', Dict[str, Any], str, bytes)

# Metrics
file_metrics = {
    'write': metrics.counter('file_ops_write_total', 'Total file writes', ['path', 'operation']),
    'read': metrics.counter('file_ops_read_total', 'Total file reads', ['path', 'operation']),
    'error': metrics.counter('file_ops_error_total', 'Total file operation errors', ['path', 'operation', 'error_type']),
    'duration': metrics.histogram('file_ops_duration_seconds', 'File operation duration', ['path', 'operation'])
}

# Lock for directory operations
_dir_lock = InterProcessLock("dreamos_dir_ops")

class FileManager(Generic[FileData]):
    """Unified file manager with atomic operations, backup support, and metrics."""
    
    def __init__(
        self,
        file_path: Union[str, Path],
        max_retries: int = 3,
        backup_enabled: bool = True,
        atomic: bool = True
    ):
        """Initialize the file manager.
        
        Args:
            file_path: Path to the managed file
            max_retries: Maximum number of retry attempts for failed operations
            backup_enabled: Whether to create backups before writes
            atomic: Whether to use atomic operations
        """
        self.file_path = Path(file_path)
        self._lock = asyncio.Lock()
        self._backup_path = self.file_path.with_suffix('.bak')
        self._temp_path = self.file_path.with_suffix('.tmp')
        self.max_retries = max_retries
        self.backup_enabled = backup_enabled
        self.atomic = atomic
        
        # Ensure directory exists
        ensure_dir(self.file_path.parent)
    
    @log_operation('file_write', metrics=file_metrics['write'], duration=file_metrics['duration'])
    async def write(self, data: FileData) -> bool:
        """Write data to file with optional atomic operation and backup.
        
        Args:
            data: Data to write (dict for JSON, str/bytes for raw)
            
        Returns:
            bool: True if write was successful
        """
        async with self._lock:
            for attempt in range(self.max_retries):
                try:
                    if self.atomic:
                        # Write to temp file first
                        if isinstance(data, dict):
                            async with aiofiles.open(self._temp_path, 'w', encoding='utf-8') as f:
                                await f.write(json.dumps(data, indent=2, default=str))
                        else:
                            async with aiofiles.open(self._temp_path, 'wb' if isinstance(data, bytes) else 'w') as f:
                                await f.write(data)
                        
                        # Backup current file if enabled and exists
                        if self.backup_enabled and self.file_path.exists():
                            os.replace(self.file_path, self._backup_path)
                        
                        # Atomic move of temp file to target
                        os.replace(self._temp_path, self.file_path)
                    else:
                        # Direct write without atomic operation
                        if isinstance(data, dict):
                            async with aiofiles.open(self.file_path, 'w', encoding='utf-8') as f:
                                await f.write(json.dumps(data, indent=2, default=str))
                        else:
                            async with aiofiles.open(self.file_path, 'wb' if isinstance(data, bytes) else 'w') as f:
                                await f.write(data)
                    
                    logger.info(
                        "file_write",
                        extra={
                            "path": str(self.file_path),
                            "bytes": len(str(data)),
                            "encoding": "utf-8" if isinstance(data, (dict, str)) else "binary"
                        }
                    )
                    return True
                    
                except Exception as e:
                    error = handle_error(e, {"path": str(self.file_path), "operation": "write"})
                    logger.error(
                        "file_write_error",
                        extra={
                            "path": str(self.file_path),
                            "error": str(error),
                            "error_type": error.__class__.__name__
                        }
                    )
                    file_metrics['error'].labels(
                        path=str(self.file_path),
                        operation="write",
                        error_type=error.__class__.__name__
                    ).inc()
                    
                    if attempt == self.max_retries - 1:
                        await self._handle_write_failure(error)
                        return False
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    @log_operation('file_read', metrics=file_metrics['read'], duration=file_metrics['duration'])
    async def read(self) -> Optional[FileData]:
        """Read data from file with backup recovery.
        
        Returns:
            Optional[FileData]: File contents or None if read fails
        """
        async with self._lock:
            try:
                # Try reading main file
                if isinstance(self.file_path.suffix, str) and self.file_path.suffix.endswith('.json'):
                    async with aiofiles.open(self.file_path, 'r', encoding='utf-8') as f:
                        content = await f.read()
                        data = json.loads(content)
                else:
                    async with aiofiles.open(self.file_path, 'rb') as f:
                        data = await f.read()
                
                logger.info(
                    "file_read",
                    extra={
                        "path": str(self.file_path),
                        "bytes": len(str(data)),
                        "encoding": "utf-8" if isinstance(data, (dict, str)) else "binary"
                    }
                )
                
                return data
                
            except FileNotFoundError:
                logger.warning(f"File {self.file_path} not found")
                return await self._recover_from_backup()
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in {self.file_path}")
                return await self._recover_from_backup()
            except Exception as e:
                error = handle_error(e, {"path": str(self.file_path), "operation": "read"})
                logger.error(
                    "file_read_error",
                    extra={
                        "path": str(self.file_path),
                        "error": str(error),
                        "error_type": error.__class__.__name__
                    }
                )
                file_metrics['error'].labels(
                    path=str(self.file_path),
                    operation="read",
                    error_type=error.__class__.__name__
                ).inc()
                return await self._recover_from_backup()
    
    @log_operation('file_recovery', metrics=file_metrics['read'], duration=file_metrics['duration'])
    async def _recover_from_backup(self) -> Optional[FileData]:
        """Attempt to recover data from backup file.
        
        Returns:
            Optional[FileData]: Recovered data or None if recovery fails
        """
        if not self._backup_path.exists():
            logger.error("No backup file available for recovery")
            return None
            
        try:
            if isinstance(self.file_path.suffix, str) and self.file_path.suffix.endswith('.json'):
                async with aiofiles.open(self._backup_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    data = json.loads(content)
            else:
                async with aiofiles.open(self._backup_path, 'rb') as f:
                    data = await f.read()
            
            # Restore backup to main file
            os.replace(self._backup_path, self.file_path)
            logger.info(f"Recovered data from backup {self._backup_path}")
            return data
            
        except Exception as e:
            error = handle_error(e, {"path": str(self._backup_path), "operation": "recovery"})
            logger.error(f"Backup recovery failed: {str(error)}")
            file_metrics['error'].labels(
                path=str(self._backup_path),
                operation="recovery",
                error_type=error.__class__.__name__
            ).inc()
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
                error = handle_error(e, {"path": str(self._backup_path), "operation": "restore"})
                logger.error(f"Failed to restore from backup: {str(error)}")
                file_metrics['error'].labels(
                    path=str(self._backup_path),
                    operation="restore",
                    error_type=error.__class__.__name__
                ).inc()
    
    @log_operation('file_validate', metrics=file_metrics['read'], duration=file_metrics['duration'])
    async def validate(self) -> bool:
        """Validate the file's structure.
        
        Returns:
            bool: True if file is valid
        """
        try:
            data = await self.read()
            if data is None:
                return False
            # Basic structure validation
            if isinstance(self.file_path.suffix, str) and self.file_path.suffix.endswith('.json'):
                return isinstance(data, dict)
            return True
        except Exception as e:
            error = handle_error(e, {"path": str(self.file_path), "operation": "validate"})
            logger.error(f"File validation failed: {str(error)}")
            file_metrics['error'].labels(
                path=str(self.file_path),
                operation="validate",
                error_type=error.__class__.__name__
            ).inc()
            return False
    
    @log_operation('file_cleanup')
    async def cleanup(self):
        """Clean up temporary files."""
        try:
            if self._temp_path.exists():
                os.remove(self._temp_path)
        except Exception as e:
            error = handle_error(e, {"path": str(self._temp_path), "operation": "cleanup"})
            logger.error(f"Failed to cleanup temp file: {str(error)}")
            file_metrics['error'].labels(
                path=str(self._temp_path),
                operation="cleanup",
                error_type=error.__class__.__name__
            ).inc()

@log_operation('mkdir')
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
            error = handle_error(e, {"path": str(path), "operation": "mkdir"})
            logger.error(
                "directory_create_permission_error",
                extra={
                    "path": str(path),
                    "error": str(error)
                }
            )
            file_metrics['error'].labels(
                path=str(path),
                operation="mkdir",
                error_type=error.__class__.__name__
            ).inc()
            raise FileOpsPermissionError(f"Permission denied: {path}") from error
        except OSError as e:
            error = handle_error(e, {"path": str(path), "operation": "mkdir"})
            logger.error(
                "directory_create_error",
                extra={
                    "path": str(path),
                    "error": str(error)
                }
            )
            file_metrics['error'].labels(
                path=str(path),
                operation="mkdir",
                error_type=error.__class__.__name__
            ).inc()
            raise FileOpsIOError(f"I/O error: {path}") from error

@log_operation('ensure_dir')
def ensure_dir(path: Union[str, Path]) -> bool:
    """Ensure directory exists with concurrency protection."""
    try:
        safe_mkdir(path)
        return True
    except Exception as e:
        error = handle_error(e, {"path": str(path), "operation": "ensure_dir"})
        logger.error(f"Error creating directory {path}: {str(error)}")
        file_metrics['error'].labels(
            path=str(path),
            operation="ensure_dir",
            error_type=error.__class__.__name__
        ).inc()
        return False

@log_operation('clear_dir')
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
        error = handle_error(e, {"path": str(path), "operation": "clear_dir"})
        logger.error(
            "directory_clear_error",
            extra={
                "path": str(path),
                "error": str(error)
            }
        )
        file_metrics['error'].labels(
            path=str(path),
            operation="clear_dir",
            error_type=error.__class__.__name__
        ).inc()
        return False

@log_operation('archive_file')
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
        error = handle_error(e, {
            "source": str(source),
            "dest": str(dest),
            "operation": "archive_file"
        })
        logger.error(
            "file_archive_error",
            extra={
                "source": str(source),
                "dest": str(dest),
                "error": str(error)
            }
        )
        file_metrics['error'].labels(
            path=str(source),
            operation="archive_file",
            error_type=error.__class__.__name__
        ).inc()
        return False

@log_operation('extract_agent_id')
def extract_agent_id(file_path: Path) -> Optional[str]:
    """Extract agent ID from a response file."""
    try:
        with open(file_path, "r") as f:
            response = json.load(f)
        return response.get("agent_id")
    except Exception as e:
        error = handle_error(e, {"path": str(file_path), "operation": "extract_agent_id"})
        logger.error(f"Error extracting agent ID from {file_path}: {str(error)}")
        file_metrics['error'].labels(
            path=str(file_path),
            operation="extract_agent_id",
            error_type=error.__class__.__name__
        ).inc()
        return None

@log_operation('backup_file')
def backup_file(
    file_path: Union[str, Path],
    backup_dir: Optional[Union[str, Path]] = None,
    move_to: Optional[Union[str, Path]] = None,
    atomic: bool = True
) -> bool:
    """Create a backup of a file and optionally move it.
    
    Args:
        file_path: Path to the file to backup
        backup_dir: Directory to store backup (defaults to same directory as file)
        move_to: Optional destination to move file after backup
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
            
        logger.info(
            "file_backed_up",
            extra={
                "path": str(file_path),
                "backup_path": str(backup_path),
                "move_to": str(move_to) if move_to else None
            }
        )
        return True
        
    except Exception as e:
        error = handle_error(e, {
            "path": str(file_path),
            "backup_dir": str(backup_dir) if backup_dir else None,
            "move_to": str(move_to) if move_to else None,
            "operation": "backup_file"
        })
        logger.error(
            "file_backup_error",
            extra={
                "path": str(file_path),
                "error": str(error)
            }
        )
        file_metrics['error'].labels(
            path=str(file_path),
            operation="backup_file",
            error_type=error.__class__.__name__
        ).inc()
        raise FileOpsError(f"File operation failed: {str(error)}") from error

@log_operation('safe_rmdir')
def safe_rmdir(path: Union[str, Path]) -> bool:
    """Safely remove a directory and its contents."""
    try:
        if os.path.exists(path):
            shutil.rmtree(path)
        return True
    except Exception as e:
        error = handle_error(e, {"path": str(path), "operation": "safe_rmdir"})
        logger.error(f"Error removing directory {path}: {str(error)}")
        file_metrics['error'].labels(
            path=str(path),
            operation="safe_rmdir",
            error_type=error.__class__.__name__
        ).inc()
        return False

@log_operation('cleanup_old_files')
async def cleanup_old_files(
    directory: Union[str, Path],
    max_age_hours: int = 24,
    pattern: str = "*.*",
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
                if await async_delete_file(filepath):
                    deleted_files.append(filepath)
        logger.info(
            "files_cleaned_up",
            extra={
                "directory": str(directory),
                "count": len(deleted_files)
            }
        )
        return deleted_files
    except Exception as e:
        error = handle_error(e, {"path": str(directory), "operation": "cleanup_old_files"})
        logger.error(
            "cleanup_old_files_error",
            extra={
                "directory": str(directory),
                "error": str(error)
            }
        )
        file_metrics['error'].labels(
            path=str(directory),
            operation="cleanup_old_files",
            error_type=error.__class__.__name__
        ).inc()
        return []

@log_operation('read_json')
def read_json(path: str | Path) -> Any:
    path = Path(path)
    if not path.exists():
        logger.warning(f"read_json: file not found: {path}")
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        error = handle_error(e, {"path": str(path), "operation": "read_json"})
        logger.error(f"read_json error: {str(error)}")
        file_metrics['error'].labels(
            path=str(path),
            operation="read_json",
            error_type=error.__class__.__name__
        ).inc()
        return None

@log_operation('write_json')
def write_json(path: str | Path, data: Any, atomic: bool = True) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        if atomic:
            tmp_path = path.with_suffix(".tmp")
            with tmp_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            tmp_path.replace(path)
        else:
            with path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
    except Exception as e:
        error = handle_error(e, {"path": str(path), "operation": "write_json"})
        logger.error(f"write_json error: {str(error)}")
        file_metrics['error'].labels(
            path=str(path),
            operation="write_json",
            error_type=error.__class__.__name__
        ).inc()
        raise FileOpsError(f"Failed to write JSON file: {str(error)}") from error

@log_operation('read_text')
def read_text(path: str | Path) -> Optional[str]:
    try:
        with Path(path).open("r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        error = handle_error(e, {"path": str(path), "operation": "read_text"})
        logger.error(f"read_text error: {str(error)}")
        file_metrics['error'].labels(
            path=str(path),
            operation="read_text",
            error_type=error.__class__.__name__
        ).inc()
        return None

@log_operation('write_text')
def write_text(path: str | Path, text: str, atomic: bool = True) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        if atomic:
            tmp_path = path.with_suffix(".tmp")
            with tmp_path.open("w", encoding="utf-8") as f:
                f.write(text)
            tmp_path.replace(path)
        else:
            with path.open("w", encoding="utf-8") as f:
                f.write(text)
    except Exception as e:
        error = handle_error(e, {"path": str(path), "operation": "write_text"})
        logger.error(f"write_text error: {str(error)}")
        file_metrics['error'].labels(
            path=str(path),
            operation="write_text",
            error_type=error.__class__.__name__
        ).inc()
        raise FileOpsError(f"Failed to write text file: {str(error)}") from error

@log_operation('copy_file')
def copy_file(src: str | Path, dest: str | Path) -> None:
    try:
        shutil.copy2(str(src), str(dest))
        logger.info(f"Copied {src} → {dest}")
    except Exception as e:
        error = handle_error(e, {
            "source": str(src),
            "dest": str(dest),
            "operation": "copy_file"
        })
        logger.error(f"copy_file error: {str(error)}")
        file_metrics['error'].labels(
            path=str(src),
            operation="copy_file",
            error_type=error.__class__.__name__
        ).inc()
        raise FileOpsError(f"Failed to copy file: {str(error)}") from error

@log_operation('safe_delete')
def safe_delete(path: str | Path) -> None:
    try:
        Path(path).unlink()
        logger.info(f"Deleted file: {path}")
    except FileNotFoundError:
        logger.debug(f"File not found: {path}")
    except Exception as e:
        error = handle_error(e, {"path": str(path), "operation": "safe_delete"})
        logger.warning(f"Failed to delete file {path}: {str(error)}")
        file_metrics['error'].labels(
            path=str(path),
            operation="safe_delete",
            error_type=error.__class__.__name__
        ).inc()
