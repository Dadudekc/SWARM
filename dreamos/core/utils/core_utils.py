"""
Core Utilities
------------
Core utility functions for the system.
"""

import os
import tempfile
import json
import shutil
from typing import Any, Optional, Dict, Tuple, Union
from pathlib import Path
from datetime import datetime

def ensure_dir(path: Union[str, Path]) -> None:
    """Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Path to the directory
    """
    os.makedirs(path, exist_ok=True)

def atomic_write(filepath: str, content: str, mode: str = 'w') -> None:
    """
    Write content to file atomically.
    
    Args:
        filepath: Path to write to
        content: Content to write
        mode: File open mode
    """
    path = Path(filepath)
    temp = tempfile.NamedTemporaryFile(mode=mode, delete=False, dir=path.parent)
    try:
        temp.write(content)
        temp.close()
        os.replace(temp.name, path)
    except Exception:
        os.unlink(temp.name)
        raise

def safe_read(file_path: Union[str, Path]) -> Optional[str]:
    """Safely read a file's contents.
    
    Args:
        file_path: Path to file
        
    Returns:
        File contents or None if error
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return None

def safe_write(file_path: Union[str, Path], content: str) -> bool:
    """Safely write content to a file.
    
    Args:
        file_path: Path to file
        content: Content to write
        
    Returns:
        True if successful
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception:
        return False

def load_json(file_path: str) -> dict:
    """Load JSON data from a file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        dict: The loaded JSON data
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in {file_path}: {str(e)}", e.doc, e.pos)

def save_json(file_path: str, data: dict, indent: int = 4) -> None:
    """Save data to a JSON file.
    
    Args:
        file_path: Path to save the JSON file
        data: Data to save
        indent: Number of spaces for indentation
        
    Raises:
        OSError: If the file cannot be written
        TypeError: If the data cannot be serialized to JSON
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent)
    except (OSError, TypeError) as e:
        raise type(e)(f"Failed to save JSON to {file_path}: {str(e)}")

def read_json(file_path: str) -> dict:
    """Alias for load_json for backward compatibility."""
    return load_json(file_path)

def backup_file(file_path: str, backup_dir: str = None) -> str:
    """Create a backup of a file.
    
    Args:
        file_path: Path to the file to backup
        backup_dir: Optional directory to store the backup. If None, creates
                   a backup in the same directory as the original file.
                   
    Returns:
        str: Path to the backup file
        
    Raises:
        FileNotFoundError: If the source file doesn't exist
        OSError: If the backup operation fails
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Source file not found: {file_path}")
        
    if backup_dir is None:
        backup_dir = os.path.dirname(file_path)
        
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.basename(file_path)
    backup_path = os.path.join(backup_dir, f"{filename}.{timestamp}.bak")
    
    shutil.copy2(file_path, backup_path)
    return backup_path

def transform_coordinates(x: int, y: int, scale: float = 1.0) -> Tuple[int, int]:
    """Transform screen coordinates.
    
    Args:
        x: X coordinate
        y: Y coordinate
        scale: Scale factor
        
    Returns:
        Transformed (x, y) coordinates
    """
    return (int(x * scale), int(y * scale))

def ensure_dir(directory: Union[str, Path]) -> None:
    """Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Path to the directory to ensure exists
    """
    os.makedirs(directory, exist_ok=True) 