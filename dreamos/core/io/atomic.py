"""
Atomic file operations module.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)

def safe_read(file_path: str | Path) -> str:
    """Read file contents safely.
    
    Args:
        file_path: Path to read from
        
    Returns:
        File contents as string
        
    Raises:
        FileNotFoundError: If file doesn't exist
        OSError: If file cannot be read
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except OSError as e:
        logger.error(f"Failed to read {file_path}: {e}")
        raise

def safe_write(
    content: str,
    file_path: str | Path,
    backup: bool = True,
    ensure_dir: bool = True
) -> None:
    """Write content to file safely using atomic operations.
    
    Args:
        content: Content to write
        file_path: Path to write to
        backup: Whether to create backup of existing file
        ensure_dir: Whether to create parent directories
        
    Raises:
        OSError: If file cannot be written
    """
    path = Path(file_path)
    if ensure_dir:
        path.parent.mkdir(parents=True, exist_ok=True)
        
    # Create backup if requested and file exists
    if backup and path.exists():
        backup_path = path.with_suffix(path.suffix + '.bak')
        try:
            shutil.copy2(path, backup_path)
        except OSError as e:
            logger.warning(f"Failed to create backup of {file_path}: {e}")
            
    # Write to temporary file first
    try:
        with tempfile.NamedTemporaryFile(
            mode='w',
            encoding='utf-8',
            delete=False,
            dir=path.parent
        ) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)
            
        # Atomic rename
        os.replace(tmp_path, path)
        
    except OSError as e:
        # Clean up temp file if it exists
        if 'tmp_path' in locals() and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        logger.error(f"Failed to write to {file_path}: {e}")
        raise 
