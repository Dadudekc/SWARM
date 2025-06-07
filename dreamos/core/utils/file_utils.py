"""
File Utilities
------------
Core file operations for Dream.OS system.
"""

import json
import logging
import os
import shutil
import yaml
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)

def atomic_write(file_path: Union[str, Path], content: str, mode: str = 'w') -> bool:
    """Write content to file atomically.
    
    Args:
        file_path: Path to write to
        content: Content to write
        mode: File open mode
        
    Returns:
        True if successful, False otherwise
    """
    try:
        temp_path = f"{file_path}.tmp"
        with open(temp_path, mode) as f:
            f.write(content)
        os.replace(temp_path, file_path)
        return True
    except Exception as e:
        logger.error(f"Error in atomic write to {file_path}: {e}")
        return False

def safe_read(file_path: Union[str, Path], default: Any = None) -> Any:
    """Safely read content from file.
    
    Args:
        file_path: Path to read from
        default: Default value if read fails
        
    Returns:
        File content or default value
    """
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return default

def safe_write(file_path: Union[str, Path], content: str) -> bool:
    """Safely write content to file.
    
    Args:
        file_path: Path to write to
        content: Content to write
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"Error writing to {file_path}: {e}")
        return False

def load_json(file_path: Union[str, Path], default: Any = None) -> Any:
    """Load JSON data from file.
    
    Args:
        file_path: Path to JSON file
        default: Default value if load fails
        
    Returns:
        Loaded JSON data or default value
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON from {file_path}: {e}")
        return default

def save_json(file_path: Union[str, Path], data: Any) -> bool:
    """Save data to JSON file.
    
    Args:
        file_path: Path to save JSON file
        data: Data to save
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving JSON to {file_path}: {e}")
        return False

def ensure_dir(path: Union[str, Path]) -> bool:
    """Ensure directory exists.
    
    Args:
        path: Directory path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {path}: {e}")
        return False

def clear_dir(path: Union[str, Path]) -> bool:
    """Clear directory contents.
    
    Args:
        path: Directory path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        for item in Path(path).glob("*"):
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        return True
    except Exception as e:
        logger.error(f"Error clearing directory {path}: {e}")
        return False

def archive_file(file_path: Path, archive_dir: Path, logger: Optional[logging.Logger] = None) -> bool:
    """Archive a file to the specified directory.
    
    Args:
        file_path: Path to the file to archive
        archive_dir: Directory to archive to
        logger: Optional logger instance
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create archive directory if it doesn't exist
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Move to archive
        archive_path = archive_dir / file_path.name
        file_path.rename(archive_path)
        
        # Log success
        if logger:
            logger.info(
                platform="file_ops",
                status="archived",
                message=f"Archived file {file_path.name}",
                tags=["archive", "success"]
            )
        return True
        
    except Exception as e:
        # Log error
        if logger:
            logger.error(
                platform="file_ops",
                status="error",
                message=f"Error archiving file {file_path}: {e}",
                tags=["archive", "error"]
            )
        return False

def extract_agent_id(file_path: Path) -> Optional[str]:
    """Extract agent ID from a response file.
    
    Args:
        file_path: Path to the response file
        
    Returns:
        Agent ID if found, None otherwise
    """
    try:
        with open(file_path, 'r') as f:
            response = json.load(f)
        return response.get("agent_id")
    except Exception as e:
        logger.error(f"Error extracting agent ID from {file_path}: {e}")
        return None

def read_json(file_path: Union[str, Path], default: Any = None) -> Any:
    """Read JSON data from file.
    
    Args:
        file_path: Path to JSON file
        default: Default value if read fails
        
    Returns:
        Loaded JSON data or default value
    """
    return load_json(file_path, default)

def backup_file(file_path: Union[str, Path], backup_dir: Union[str, Path], logger: Optional[logging.Logger] = None) -> bool:
    """Create a backup of a file.
    
    Args:
        file_path: Path to the file to backup
        backup_dir: Directory to store backup
        logger: Optional logger instance
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create backup directory if it doesn't exist
        backup_dir = Path(backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create backup
        backup_path = backup_dir / f"{Path(file_path).name}.bak"
        shutil.copy2(file_path, backup_path)
        
        # Log success
        if logger:
            logger.info(
                platform="file_ops",
                status="backed_up",
                message=f"Backed up file {file_path}",
                tags=["backup", "success"]
            )
        return True
        
    except Exception as e:
        # Log error
        if logger:
            logger.error(
                platform="file_ops",
                status="error",
                message=f"Error backing up file {file_path}: {e}",
                tags=["backup", "error"]
            )
        return False

def write_json(data: Any, filepath: str, indent: int = 4) -> bool:
    """Write data to a JSON file.
    
    Args:
        data: The data to write
        filepath: Path to the file
        indent: Number of spaces for indentation
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent)
        return True
    except Exception as e:
        logger.error(f"Failed to write JSON to {filepath}: {e}")
        return False

def restore_backup(backup_path: str, target_path: str) -> bool:
    """Restore a file from its backup.
    
    Args:
        backup_path: Path to the backup file
        target_path: Path where the file should be restored
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not os.path.exists(backup_path):
            logger.error(f"Backup file not found: {backup_path}")
            return False
            
        shutil.copy2(backup_path, target_path)
        logger.info(f"Restored backup from {backup_path} to {target_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to restore backup from {backup_path}: {e}")
        return False

def read_yaml(file_path: Union[str, Path], default: Any = None) -> Any:
    """Read YAML data from file.
    
    Args:
        file_path: Path to YAML file
        default: Default value if read fails
        
    Returns:
        Loaded YAML data or default value
    """
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error reading YAML from {file_path}: {e}")
        return default

def load_yaml(file_path: Union[str, Path], default: Any = None) -> Any:
    """Alias for read_yaml for backward compatibility."""
    return read_yaml(file_path, default)

def write_yaml(file_path: Union[str, Path], data: Any) -> bool:
    """Write data to YAML file.
    
    Args:
        file_path: Path to write YAML file
        data: Data to write
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(file_path, 'w') as f:
            yaml.safe_dump(data, f, default_flow_style=False)
        return True
    except Exception as e:
        logger.error(f"Error writing YAML to {file_path}: {e}")
        return False

def safe_rmdir(path: Union[str, Path]) -> bool:
    """Safely remove a directory and its contents.
    
    Args:
        path: Directory path to remove
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if os.path.exists(path):
            shutil.rmtree(path)
        return True
    except Exception as e:
        logger.error(f"Error removing directory {path}: {e}")
        return False

def save_yaml(file_path: Union[str, Path], data: Any) -> bool:
    """Save data to YAML file.
    
    Args:
        file_path: Path to save YAML file
        data: Data to save
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(file_path, 'w') as f:
            yaml.safe_dump(data, f, default_flow_style=False)
        return True
    except Exception as e:
        logger.error(f"Error saving YAML to {file_path}: {e}")
        return False 