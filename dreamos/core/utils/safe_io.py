"""Safe file I/O helpers extracted from file_utils."""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Optional, Union
from collections import Counter

import aiofiles
from fasteners import InterProcessLock

logger = logging.getLogger(__name__)

# Metrics counter for file operations
metrics = Counter()

class SafeIOError(Exception):
    """Legacy safe I/O error for compatibility."""

def atomic_write(
    file_path: Union[str, Path], 
    content: str, 
    mode: str = "w", 
    encoding: str = "utf-8"
) -> bool:
    """Write content to file atomically using a temporary file.
    
    Args:
        file_path: Path to write to
        content: Content to write
        mode: File open mode
        encoding: File encoding
        
    Returns:
        bool: True if write succeeded, False otherwise
    """
    file_path = Path(file_path)
    temp_path = None
    try:
        # Create temp file in same directory for atomic rename
        temp_path = tempfile.NamedTemporaryFile(
            mode=mode,
            encoding=encoding,
            delete=False,
            dir=file_path.parent
        )
        temp_path.write(content)
        temp_path.close()
        
        # Atomic rename
        os.replace(temp_path.name, str(file_path))
        
        # Log success
        logger.info(
            "file_write",
            extra={
                "path": str(file_path),
                "bytes": len(content),
                "encoding": encoding
            }
        )
        metrics["file_writes"] += 1
        return True
        
    except Exception as e:
        logger.error(
            "file_write_error",
            extra={
                "path": str(file_path),
                "error": str(e)
            }
        )
        metrics["file_write_errors"] += 1
        return False
        
    finally:
        # Cleanup temp file if it still exists
        if temp_path and os.path.exists(temp_path.name):
            try:
                os.unlink(temp_path.name)
            except Exception as e:
                logger.warning(
                    "temp_cleanup_failed",
                    extra={
                        "path": temp_path.name,
                        "error": str(e)
                    }
                )


def safe_read(
    file_path: Union[str, Path], 
    default: Any = None, 
    encoding: str = "utf-8"
) -> Any:
    """Safely read content from file.
    
    Args:
        file_path: Path to read from
        default: Value to return if read fails
        encoding: File encoding
        
    Returns:
        File contents or default value if read fails
    """
    file_path = Path(file_path)
    try:
        with open(file_path, "r", encoding=encoding) as f:
            content = f.read()
            
        logger.info(
            "file_read",
            extra={
                "path": str(file_path),
                "bytes": len(content),
                "encoding": encoding
            }
        )
        metrics["file_reads"] += 1
        return content
        
    except Exception as e:
        logger.error(
            "file_read_error",
            extra={
                "path": str(file_path),
                "error": str(e)
            }
        )
        metrics["file_read_errors"] += 1
        return default


def safe_write(
    file_path: Union[str, Path], 
    content: str,
    encoding: str = "utf-8"
) -> bool:
    """Safely write content to file using atomic write.
    
    Args:
        file_path: Path to write to
        content: Content to write
        encoding: File encoding
        
    Returns:
        bool: True if write succeeded, False otherwise
    """
    return atomic_write(file_path, content, "w", encoding)


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
