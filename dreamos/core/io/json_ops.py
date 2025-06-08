"""
JSON file operations module.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

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
