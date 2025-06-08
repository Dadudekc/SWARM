"""
Core utilities for messaging system.
"""

from typing import Any, Dict, List, Optional, Union
import json
import time
from datetime import datetime
import os
import yaml
from pathlib import Path
from tempfile import NamedTemporaryFile
import shutil

def format_message(message: Dict[str, Any]) -> str:
    """Format a message for display.
    
    Args:
        message: Message dictionary
        
    Returns:
        Formatted message string
    """
    content = message.get('content', '')
    if isinstance(content, dict):
        content = json.dumps(content, indent=2)
    return f"{message.get('type', 'unknown')}: {content}"

def parse_message(message_str: str) -> Dict[str, Any]:
    """Parse a message string into a dictionary.
    
    Args:
        message_str: Message string
        
    Returns:
        Message dictionary
    """
    try:
        return json.loads(message_str)
    except json.JSONDecodeError:
        return {
            'type': 'text',
            'content': message_str,
            'timestamp': time.time()
        }

def validate_message(message: Dict[str, Any]) -> bool:
    """Validate a message dictionary.
    
    Args:
        message: Message dictionary
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ['type', 'content']
    return all(field in message for field in required_fields)

def get_message_type(message: Dict[str, Any]) -> str:
    """Get the type of a message.
    
    Args:
        message: Message dictionary
        
    Returns:
        Message type
    """
    return message.get('type', 'unknown')

def get_message_content(message: Dict[str, Any]) -> Any:
    """Get the content of a message.
    
    Args:
        message: Message dictionary
        
    Returns:
        Message content
    """
    return message.get('content')

def get_message_timestamp(message: Dict[str, Any]) -> float:
    """Get the timestamp of a message.
    
    Args:
        message: Message dictionary
        
    Returns:
        Message timestamp
    """
    return message.get('timestamp', time.time())

def format_timestamp(timestamp: float) -> str:
    """Format a timestamp for display.
    
    Args:
        timestamp: Unix timestamp
        
    Returns:
        Formatted timestamp string
    """
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def write_json(data: Dict[str, Any], filepath: str, ensure_dir: bool = True) -> None:
    """Write data to a JSON file.
    
    Args:
        data: Data to write
        filepath: Path to write to
        ensure_dir: Whether to ensure directory exists
    """
    if ensure_dir:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def read_yaml(filepath: str) -> Dict[str, Any]:
    """Read data from a YAML file.
    
    Args:
        filepath: Path to read from
        
    Returns:
        Data from YAML file
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def ensure_directory_exists(path: str) -> None:
    """Ensure that a directory exists, creating it if necessary."""
    os.makedirs(path, exist_ok=True)

def atomic_write(filepath: str | Path, data: str, mode="w", encoding="utf-8"):
    """
    Safely write data to a file by first writing to a temp file and renaming.
    Prevents partial writes on crash/interruption.
    """
    filepath = Path(filepath)
    with NamedTemporaryFile(mode=mode, encoding=encoding, delete=False, dir=filepath.parent) as tmp_file:
        tmp_file.write(data)
        temp_path = Path(tmp_file.name)
    shutil.move(str(temp_path), str(filepath))

def safe_read(filepath: str | Path, mode="r", encoding="utf-8") -> str:
    """
    Safely read data from a file, handling potential file system issues.
    Returns empty string if file doesn't exist or can't be read.
    """
    try:
        filepath = Path(filepath)
        if not filepath.exists():
            return ""
        with open(filepath, mode=mode, encoding=encoding) as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading file {filepath}: {e}")
        return ""

__all__ = [
    'format_message',
    'parse_message',
    'validate_message',
    'get_message_type',
    'get_message_content',
    'get_message_timestamp',
    'format_timestamp',
    'write_json',
    'read_yaml',
    'ensure_directory_exists',
    'atomic_write',
    'safe_read'
] 
