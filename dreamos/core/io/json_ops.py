"""
JSON Operations Module

JSON file operations for the Dream.OS system.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

def read_json(file_path: str) -> Dict[str, Any]:
    """Read a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Dictionary containing the JSON data
    """
    with open(file_path) as f:
        return json.load(f)
        
def write_json(file_path: str, data: Dict[str, Any], indent: int = 2) -> None:
    """Write data to a JSON file.
    
    Args:
        file_path: Path to the JSON file
        data: Dictionary to write
        indent: Number of spaces for indentation
    """
    with open(file_path, "w") as f:
        json.dump(data, f, indent=indent)

def read_json(file_path: str | Path) -> Dict[str, Any]:
    """Read JSON from file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Parsed JSON data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"JSON file not found: {file_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        raise

def write_json(
    data: Dict[str, Any],
    file_path: str | Path,
    indent: int = 2,
    ensure_dir: bool = True
) -> None:
    """Write data to JSON file.
    
    Args:
        data: Data to write
        file_path: Path to write to
        indent: JSON indentation level
        ensure_dir: Whether to create parent directories
        
    Raises:
        OSError: If file cannot be written
    """
    path = Path(file_path)
    if ensure_dir:
        path.parent.mkdir(parents=True, exist_ok=True)
        
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent)
    except OSError as e:
        logger.error(f"Failed to write JSON to {file_path}: {e}")
        raise 
