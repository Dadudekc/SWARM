"""
Unified File Utilities
---------------------
Comprehensive file operations and utilities.
"""

import os
import json
import yaml
import shutil
from pathlib import Path
from typing import Set, Dict, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)

# File Operations

def is_valid_file(file_path: Path, valid_extensions: Set[str]) -> bool:
    """Check if a file is valid based on extension and not in ignored patterns."""
    # Ignore __pycache__ and similar patterns
    if "__pycache__" in str(file_path):
        return False
    # Check for invalid characters in the filename only
    if any(char in file_path.name for char in ["*", "?", ":"]):
        return False
    return get_file_extension(file_path).lower() in {ext.lower() for ext in valid_extensions}

def is_test_file(file_path: Path) -> bool:
    """Check if a file is a test file based on naming patterns and location."""
    path_str = str(file_path).replace("\\", "/")
    name = file_path.name
    stem = file_path.stem
    name_lower = name.lower()
    stem_lower = stem.lower()

    # 1. In a 'tests' directory
    if "/tests/" in path_str.lower() or path_str.lower().startswith("tests/"):
        return True

    # 2. Suffixes for .py files
    for suffix in ("_test.py", "_spec.py", "_suite.py"):
        if name_lower.endswith(suffix):
            return True

    # 3. Test prefix for .py files (case-insensitive, not all lowercase)
    if name_lower.endswith('.py') and stem_lower.startswith('test') and stem != stem_lower:
        return True

    # 4. .pyc/.pyo logic
    if name_lower.endswith('.pyc') or name_lower.endswith('.pyo'):
        if name_lower.startswith('test_'):
            return True
        for pattern in ("_test", "_spec", "_suite"):
            if stem_lower.endswith(pattern):
                return True

    return False

def get_file_extension(file_path: Path) -> str:
    """Get the file extension from a file path."""
    return file_path.suffix

def normalize_path(file_path: Path) -> Path:
    """Return the path unchanged if it is relative, else resolve."""
    if not file_path.is_absolute():
        if any(char in file_path.name for char in ["*", "?", ":"]):
            raise ValueError("Path contains invalid characters")
        return file_path
    return file_path.resolve()

def ensure_dir(directory: Path) -> None:
    """Create a directory and all parent directories if they do not exist."""
    try:
        # Check for invalid characters in the last component only
        if any(char in directory.name for char in ["*", "?", ":"]):
            raise ValueError("Path contains invalid characters")
        # Check for max length (Windows has a 260 character limit)
        if len(str(directory)) > 260:
            raise ValueError("Path exceeds maximum length")
        directory.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        raise PermissionError(f"Permission denied: {directory}")
    except OSError as e:
        if e.errno == 13:  # Permission denied
            raise PermissionError(f"Permission denied: {directory}")
        raise

def clean_dir(directory: Path) -> None:
    """Remove all files and subdirectories from a directory."""
    if not directory.exists():
        return
    for item in directory.iterdir():
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)

def safe_mkdir(directory: Path) -> None:
    """Safely create a directory, handling race conditions."""
    try:
        ensure_dir(directory)
    except FileExistsError:
        pass

def safe_rmdir(directory: Path) -> None:
    """Safely remove a directory and its contents."""
    if directory.exists():
        shutil.rmtree(directory)

# File I/O Operations

def read_file(file_path: Path, encoding: str = 'utf-8') -> str:
    """Read a file's contents."""
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise

def write_file(file_path: Path, content: str, encoding: str = 'utf-8') -> None:
    """Write content to a file."""
    try:
        ensure_dir(file_path.parent)
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
    except Exception as e:
        logger.error(f"Error writing file {file_path}: {e}")
        raise

def read_json(file_path: Path) -> Dict[str, Any]:
    """Read and parse a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading JSON file {file_path}: {e}")
        raise

def write_json(file_path: Path, data: Dict[str, Any], indent: int = 2) -> None:
    """Write data to a JSON file."""
    try:
        ensure_dir(file_path.parent)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent)
    except Exception as e:
        logger.error(f"Error writing JSON file {file_path}: {e}")
        raise

def read_yaml(file_path: Path) -> Dict[str, Any]:
    """Read and parse a YAML file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error reading YAML file {file_path}: {e}")
        raise

def write_yaml(file_path: Path, data: Dict[str, Any]) -> None:
    """Write data to a YAML file."""
    try:
        ensure_dir(file_path.parent)
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(data, f, default_flow_style=False)
    except Exception as e:
        logger.error(f"Error writing YAML file {file_path}: {e}")
        raise

# File Management

def backup_file(file_path: Path, backup_dir: Optional[Path] = None) -> Path:
    """Create a backup of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    if backup_dir is None:
        backup_dir = file_path.parent / "backups"
    ensure_dir(backup_dir)
    
    backup_path = backup_dir / f"{file_path.stem}_{file_path.suffix[1:]}.bak"
    shutil.copy2(file_path, backup_path)
    return backup_path

def archive_file(file_path: Path, archive_dir: Optional[Path] = None) -> Path:
    """Archive a file by moving it to an archive directory."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    if archive_dir is None:
        archive_dir = file_path.parent / "archive"
    ensure_dir(archive_dir)
    
    archive_path = archive_dir / file_path.name
    shutil.move(file_path, archive_path)
    return archive_path

def extract_agent_id(file_path: Path) -> Optional[str]:
    """Extract agent ID from a file path."""
    try:
        # Try to find agent ID in path
        parts = str(file_path).split(os.sep)
        for part in parts:
            if part.startswith("agent_") and len(part) > 6:
                return part[6:]
        return None
    except Exception:
        return None 