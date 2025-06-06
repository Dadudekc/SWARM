"""
File System Utilities
-------------------
Robust file system operations with Windows compatibility.
"""

import os
import json
import yaml
import logging
import tempfile
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from contextlib import contextmanager
from datetime import datetime

logger = logging.getLogger(__name__)

class FileOpsError(Exception):
    """Base exception for file operations."""
    pass

class FileOpsPermissionError(FileOpsError):
    """Raised when a file operation fails due to permission issues."""
    pass

class FileOpsIOError(FileOpsError):
    """Raised when a file operation fails due to I/O issues."""
    pass

@contextmanager
def safe_file_handle(file_path: Union[str, Path], mode: str = 'r'):
    """Safely handle file operations with proper cleanup.
    
    Args:
        file_path: Path to the file
        mode: File open mode
    """
    file_path = Path(file_path)
    temp_path = None
    try:
        # Create temp file for writing
        if 'w' in mode or 'a' in mode:
            temp_path = tempfile.NamedTemporaryFile(delete=False)
            temp_path.close()
            yield temp_path.name
            # Atomic move on Windows
            shutil.move(temp_path.name, str(file_path))
        else:
            # For reading, just open the file
            with open(file_path, mode) as f:
                yield f
    except Exception as e:
        logger.error(f"File operation failed: {e}")
        raise
    finally:
        # Cleanup temp file if it exists
        if temp_path and os.path.exists(temp_path.name):
            try:
                os.unlink(temp_path.name)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file: {e}")

@contextmanager
def atomic_write(file_path: Union[str, Path], mode: str = 'w', encoding: str = 'utf-8'):
    """Atomically write to a file using a temporary file.
    
    Args:
        file_path: Path to write to
        mode: File open mode
        encoding: File encoding
    """
    file_path = Path(file_path)
    temp_path = None
    try:
        # Create temp file
        temp_path = tempfile.NamedTemporaryFile(delete=False, mode=mode, encoding=encoding)
        yield temp_path
        temp_path.close()
        # Atomic move on Windows
        shutil.move(temp_path.name, str(file_path))
    except Exception as e:
        logger.error(f"Atomic write failed: {e}")
        raise
    finally:
        # Cleanup temp file if it exists
        if temp_path and os.path.exists(temp_path.name):
            try:
                os.unlink(temp_path.name)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file: {e}")

def safe_write(file_path: Union[str, Path], content: str, encoding: str = 'utf-8') -> bool:
    """Safely write content to a file.
    
    Args:
        file_path: Path to write to
        content: Content to write
        encoding: File encoding
        
    Returns:
        True if successful
    """
    file_path = Path(file_path)
    try:
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with safe_file_handle(file_path, 'w') as f:
            with open(f, 'w', encoding=encoding) as fp:
                fp.write(content)
        return True
    except Exception as e:
        logger.error(f"Failed to write file {file_path}: {e}")
        return False

def safe_read(file_path: Union[str, Path], encoding: str = 'utf-8') -> Optional[str]:
    """Safely read content from a file.
    
    Args:
        file_path: Path to read from
        encoding: File encoding
        
    Returns:
        File content or None if failed
    """
    file_path = Path(file_path)
    try:
        with safe_file_handle(file_path, 'r') as f:
            with open(f, 'r', encoding=encoding) as fp:
                return fp.read()
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        return None

def load_json(file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """Load JSON from file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Parsed JSON or None if failed
    """
    content = safe_read(file_path)
    if content is None:
        return None
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from {file_path}: {e}")
        return None

def save_json(file_path: Union[str, Path], data: Dict[str, Any], indent: int = 2) -> bool:
    """Save data as JSON.
    
    Args:
        file_path: Path to save to
        data: Data to save
        indent: JSON indentation
        
    Returns:
        True if successful
    """
    try:
        content = json.dumps(data, indent=indent)
        return safe_write(file_path, content)
    except Exception as e:
        logger.error(f"Failed to save JSON to {file_path}: {e}")
        return False

def load_yaml(file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """Load YAML from file.
    
    Args:
        file_path: Path to YAML file
        
    Returns:
        Parsed YAML or None if failed
    """
    content = safe_read(file_path)
    if content is None:
        return None
    try:
        return yaml.safe_load(content)
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML from {file_path}: {e}")
        return None

def save_yaml(file_path: Union[str, Path], data: Dict[str, Any]) -> bool:
    """Save data as YAML.
    
    Args:
        file_path: Path to save to
        data: Data to save
        
    Returns:
        True if successful
    """
    try:
        content = yaml.dump(data, default_flow_style=False)
        return safe_write(file_path, content)
    except Exception as e:
        logger.error(f"Failed to save YAML to {file_path}: {e}")
        return False

def ensure_dir(dir_path: Union[str, Path]) -> bool:
    """Ensure directory exists.
    
    Args:
        dir_path: Directory path
        
    Returns:
        True if successful
    """
    try:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {dir_path}: {e}")
        return False

def cleanup_old_files(dir_path: Union[str, Path], pattern: str, max_age_days: int = 30) -> None:
    """Clean up old files.
    
    Args:
        dir_path: Directory to clean
        pattern: File pattern to match
        max_age_days: Maximum file age in days
    """
    try:
        dir_path = Path(dir_path)
        if not dir_path.exists():
            return
            
        for file_path in dir_path.glob(pattern):
            if file_path.is_file():
                age = (datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)).days
                if age > max_age_days:
                    try:
                        file_path.unlink()
                    except Exception as e:
                        logger.warning(f"Failed to delete old file {file_path}: {e}")
    except Exception as e:
        logger.error(f"Failed to cleanup old files in {dir_path}: {e}")

def find_files(dir_path: Union[str, Path], pattern: str) -> List[Path]:
    """Find files matching pattern.
    
    Args:
        dir_path: Directory to search
        pattern: File pattern to match
        
    Returns:
        List of matching file paths
    """
    try:
        return list(Path(dir_path).glob(pattern))
    except Exception as e:
        logger.error(f"Failed to find files in {dir_path}: {e}")
        return []

def read_json(path: Union[str, Path], default: Any = None) -> Dict[str, Any]:
    """Read JSON from a file.
    
    Args:
        path: File path to read from
        default: Default value to return if file doesn't exist or is invalid
        
    Returns:
        Parsed JSON data or default value
        
    Raises:
        FileOpsError: If file doesn't exist and no default provided
        FileOpsIOError: If file exists but contains invalid JSON
    """
    path = Path(path)
    if not path.exists():
        if default is not None:
            return default
        raise FileOpsError(f"File not found: {path}")
        
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, Exception) as e:
        if default is not None:
            return default
        raise FileOpsIOError(f"Invalid JSON in {path}: {e}")

def write_json(path: Union[str, Path], data: dict) -> None:
    """Write JSON to a file.
    
    Args:
        path: File path to write to
        data: Data to write
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def read_yaml(path: Union[str, Path], default: Any = None) -> Any:
    """Read YAML from a file.
    
    Args:
        path: File path to read from
        default: Default value to return if file doesn't exist or is invalid
        
    Returns:
        Loaded YAML data or default value
        
    Raises:
        FileOpsError: If file doesn't exist and no default provided
        FileOpsIOError: If file exists but contains invalid YAML
    """
    path = Path(path)
    if not path.exists():
        if default is not None:
            return default
        raise FileOpsError(f"File not found: {path}")
        
    try:
        with open(path) as f:
            content = f.read()
            if not content.strip():  # Empty or whitespace-only file
                return default if default is not None else {}
            # Use strict YAML loading
            try:
                return yaml.safe_load(content)
            except yaml.YAMLError as e:
                # Double check with a more strict parser
                try:
                    yaml.scanner.Scanner(content)
                    yaml.parser.Parser(content)
                except Exception as e2:
                    if default is not None:
                        return default
                    raise FileOpsIOError(f"Invalid YAML in {path}: {e2}")
                # If we get here, the YAML is actually valid
                return yaml.safe_load(content)
    except Exception as e:
        if default is not None:
            return default
        raise FileOpsIOError(f"Error reading YAML from {path}: {e}")

def write_yaml(path: Union[str, Path], data: dict) -> None:
    """Write YAML to a file.
    
    Args:
        path: File path to write to
        data: Data to write
        
    Raises:
        FileOpsPermissionError: If file is read-only or permission denied
        FileOpsIOError: If I/O error occurs
    """
    try:
        with open(path, 'w') as f:
            yaml.safe_dump(data, f, default_flow_style=False)
    except PermissionError as e:
        raise FileOpsPermissionError(f"Permission denied: {path}") from e
    except IOError as e:
        raise FileOpsIOError(f"I/O error: {path}") from e

def safe_rmdir(path: Union[str, Path], recursive: bool = False) -> None:
    """Safely remove a directory.
    
    Args:
        path: Directory path to remove
        recursive: If True, recursively remove directory contents
        
    Raises:
        FileOpsError: If directory is not empty and recursive=False
        FileOpsPermissionError: If permission denied
        FileOpsIOError: If I/O error occurs
    """
    path = Path(path)
    if not path.exists():
        return
        
    try:
        if recursive:
            shutil.rmtree(path)
        else:
            if any(path.iterdir()):
                raise FileOpsError(f"Directory not empty: {path}")
            path.rmdir()
    except PermissionError as e:
        raise FileOpsPermissionError(f"Permission denied: {path}") from e
    except IOError as e:
        raise FileOpsIOError(f"I/O error: {path}") from e

def safe_mkdir(path: Union[str, Path]) -> None:
    """Safely create a directory.
    
    Args:
        path: Path to create
    """
    path = Path(path)
    if not path.exists():
        path.mkdir(parents=True)

def safe_remove(path: Union[str, Path], recursive: bool = False) -> bool:
    """Safely remove a file or directory.
    
    Args:
        path: Path to the file or directory to remove
        recursive: If True, recursively remove directories
        
    Returns:
        bool: True if removal was successful
    """
    try:
        path = Path(path)
        if not path.exists():
            logger.warning(f"Path does not exist: {path}")
            return True
            
        if path.is_dir():
            if recursive:
                shutil.rmtree(path)
            else:
                logger.error(f"Cannot remove directory without recursive=True: {path}")
                return False
        else:
            os.remove(path)
            
        return True
        
    except Exception as e:
        logger.exception(f"Error removing {path}: {e}")
        return False

def safe_copy(src: Union[str, Path], dst: Union[str, Path], overwrite: bool = False) -> bool:
    """Safely copy a file.
    
    Args:
        src: Source file path
        dst: Destination file path
        overwrite: If True, overwrite existing file
        
    Returns:
        bool: True if copy was successful
    """
    try:
        src = Path(src)
        dst = Path(dst)
        
        if not src.exists():
            logger.error(f"Source file does not exist: {src}")
            return False
            
        if dst.exists() and not overwrite:
            logger.error(f"Destination file exists and overwrite=False: {dst}")
            return False
            
        # Create parent directories if they don't exist
        dst.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(src, dst)
        return True
        
    except Exception as e:
        logger.exception(f"Error copying {src} to {dst}: {e}")
        return False

def safe_move(src: Union[str, Path], dst: Union[str, Path], overwrite: bool = False) -> bool:
    """Safely move a file or directory.
    
    Args:
        src: Source path
        dst: Destination path
        overwrite: If True, overwrite existing file/directory
        
    Returns:
        bool: True if move was successful
    """
    try:
        src = Path(src)
        dst = Path(dst)
        
        if not src.exists():
            logger.error(f"Source path does not exist: {src}")
            return False
            
        if dst.exists() and not overwrite:
            logger.error(f"Destination path exists and overwrite=False: {dst}")
            return False
            
        # Create parent directories if they don't exist
        dst.parent.mkdir(parents=True, exist_ok=True)
        
        # Move the file/directory
        shutil.move(str(src), str(dst))
        return True
        
    except Exception as e:
        logger.exception(f"Error moving {src} to {dst}: {e}")
        return False

def rotate_file(path: Union[str, Path], max_size: int = 10 * 1024 * 1024, max_files: int = 5) -> None:
    """Rotate a file if it exceeds max_size.
    
    Args:
        path: File path to rotate
        max_size: Maximum file size in bytes
        max_files: Maximum number of rotated files to keep
        
    Raises:
        FileOpsError: If file doesn't exist
        FileOpsIOError: If rotation fails
    """
    path = Path(path)
    if not path.exists():
        raise FileOpsError(f"File not found: {path}")
        
    # Check if rotation is needed
    if path.stat().st_size < max_size:
        return
        
    # Step 1: Rename existing backups upward
    for i in range(max_files - 1, 0, -1):
        older = path.with_suffix(f"{path.suffix}.{i - 1}" if i - 1 else path.suffix)
        newer = path.with_suffix(f"{path.suffix}.{i}")
        if older.exists():
            older.replace(newer)
                
    try:
        # Step 2: Rename current file to .1
        backup = path.with_suffix(f"{path.suffix}.1")
        try:
            path.replace(backup)
        except PermissionError:
            # On Windows, file might still be locked briefly. Retry a few times.
            for _ in range(3):
                time.sleep(0.05)
                try:
                    path.replace(backup)
                    break
                except PermissionError:
                    continue

        # Step 3: If the original still exists (handle Windows race), delete it
        if path.exists():
            try:
                path.unlink()
            except PermissionError:
                # Retry once more if still locked
                time.sleep(0.05)
                if path.exists():
                    path.unlink()

        # Step 4: Create a fresh empty file at the original path
        path.write_text("")
    except Exception as e:
        raise FileOpsIOError(f"Failed to rotate file {path}: {e}")

def backup_file(path: Union[str, Path], backup_suffix: str = '.bak') -> Optional[Path]:
    """Create a backup of a file.
    
    Args:
        path: Path to the file to backup
        backup_suffix: Suffix for the backup file
        
    Returns:
        Path to the backup file if successful, None otherwise
        
    Raises:
        FileOpsError: If file doesn't exist
        FileOpsPermissionError: If permission denied
        FileOpsIOError: If I/O error occurs
    """
    path = Path(path)
    if not path.exists():
        raise FileOpsError(f"File not found: {path}")
        
    backup_path = path.with_suffix(backup_suffix)
    try:
        shutil.copy2(path, backup_path)
        return backup_path
    except PermissionError as e:
        raise FileOpsPermissionError(f"Permission denied: {path}") from e
    except IOError as e:
        raise FileOpsIOError(f"I/O error: {path}") from e

def restore_backup(path: Union[str, Path], backup_suffix: str = '.bak') -> bool:
    """Restore a file from its backup.
    
    Args:
        path: Path to the file to restore
        backup_suffix: Suffix of the backup file
        
    Returns:
        True if restore was successful
        
    Raises:
        FileOpsError: If backup doesn't exist
        FileOpsPermissionError: If permission denied
        FileOpsIOError: If I/O error occurs
    """
    path = Path(path)
    backup_path = path.with_suffix(backup_suffix)
    
    if not backup_path.exists():
        raise FileOpsError(f"Backup not found: {backup_path}")
        
    try:
        shutil.copy2(backup_path, path)
        return True
    except PermissionError as e:
        raise FileOpsPermissionError(f"Permission denied: {path}") from e
    except IOError as e:
        raise FileOpsIOError(f"I/O error: {path}") from e 