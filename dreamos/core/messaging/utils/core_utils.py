"""
Core utilities for messaging system.
"""

from typing import Any, Dict, List, Optional, Union
import json
import time
from datetime import datetime
import os
import yaml
import shutil
from pathlib import Path

def ensure_directory_exists(directory: str) -> None:
    """Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Directory path to ensure exists
    """
    os.makedirs(directory, exist_ok=True)

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

def atomic_write(filepath: str, content: str, encoding: str = 'utf-8') -> None:
    """Write content to a file atomically.
    
    Args:
        filepath: Path to write to
        content: Content to write
        encoding: File encoding
    """
    temp_path = f"{filepath}.tmp"
    try:
        with open(temp_path, 'w', encoding=encoding) as f:
            f.write(content)
        os.replace(temp_path, filepath)
    except Exception:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise

def safe_read(filepath: str, default: Any = None, encoding: str = 'utf-8') -> Any:
    """Safely read content from a file.
    
    Args:
        filepath: Path to read from
        default: Default value if file doesn't exist
        encoding: File encoding
        
    Returns:
        File content or default value
    """
    try:
        with open(filepath, 'r', encoding=encoding) as f:
            return f.read()
    except FileNotFoundError:
        return default

def safe_write(filepath: str, content: str, encoding: str = 'utf-8') -> None:
    """Safely write content to a file.
    
    Args:
        filepath: Path to write to
        content: Content to write
        encoding: File encoding
    """
    ensure_directory_exists(os.path.dirname(filepath))
    atomic_write(filepath, content, encoding)

def load_json(filepath: str, default: Any = None) -> Any:
    """Load JSON data from a file.
    
    Args:
        filepath: Path to read from
        default: Default value if file doesn't exist
        
    Returns:
        JSON data or default value
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def save_json(data: Any, filepath: str) -> None:
    """Save data to a JSON file.
    
    Args:
        data: Data to save
        filepath: Path to write to
    """
    ensure_directory_exists(os.path.dirname(filepath))
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def ensure_dir(directory: str) -> None:
    """Ensure a directory exists.
    
    Args:
        directory: Directory path to ensure exists
    """
    os.makedirs(directory, exist_ok=True)

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
    'safe_read',
    'safe_write',
    'load_json',
    'save_json',
    'ensure_dir'
] 