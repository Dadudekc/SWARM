"""Utility functions for file operations."""

from pathlib import Path
from typing import Set
import os

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
    """
    Check if a file is a test file based on:
    1. Being in a 'tests' directory (anywhere in the path)
    2. Having a suffix: '_test.py', '_spec.py', or '_suite.py' (case-insensitive)
    3. For .py files, having a stem that starts with 'test' (case-insensitive) and is not all lowercase
    4. For .pyc/.pyo files, having a name that starts with 'test_' or stem ending with '_test', '_spec', or '_suite'
    """
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

def create_directory(directory: Path) -> None:
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
