import os
import shutil
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union

from .exceptions import FileOpsError, FileOpsPermissionError, FileOpsIOError

logger = logging.getLogger(__name__)


def ensure_dir(dir_path: Union[str, Path]) -> bool:
    """Ensure directory exists."""
    try:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f'Failed to create directory {dir_path}: {e}')
        return False

def cleanup_old_files(dir_path: Union[str, Path], pattern: str, max_age_days: int = 30) -> None:
    """Clean up old files."""
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
                        logger.warning(f'Failed to delete old file {file_path}: {e}')
    except Exception as e:
        logger.error(f'Failed to cleanup old files in {dir_path}: {e}')

def find_files(dir_path: Union[str, Path], pattern: str) -> List[Path]:
    """Find files matching pattern."""
    try:
        return list(Path(dir_path).glob(pattern))
    except Exception as e:
        logger.error(f'Failed to find files in {dir_path}: {e}')
        return []

def safe_rmdir(path: Union[str, Path], recursive: bool = False) -> None:
    """Safely remove a directory."""
    path = Path(path)
    if not path.exists():
        return
    try:
        if recursive:
            shutil.rmtree(path)
        else:
            if any(path.iterdir()):
                raise FileOpsError(f'Directory not empty: {path}')
            path.rmdir()
    except PermissionError as e:
        raise FileOpsPermissionError(f'Permission denied: {path}') from e
    except IOError as e:
        raise FileOpsIOError(f'I/O error: {path}') from e

def safe_mkdir(path: Union[str, Path]) -> None:
    """Safely create a directory."""
    path = Path(path)
    if not path.exists():
        path.mkdir(parents=True)

def safe_remove(path: Union[str, Path], recursive: bool = False) -> bool:
    """Safely remove a file or directory."""
    try:
        path = Path(path)
        if not path.exists():
            logger.warning(f'Path does not exist: {path}')
            return True
        if path.is_dir():
            if recursive:
                shutil.rmtree(path)
            else:
                logger.error(f'Cannot remove directory without recursive=True: {path}')
                return False
        else:
            os.remove(path)
        return True
    except Exception as e:
        logger.exception(f'Error removing {path}: {e}')
        return False

def safe_copy(src: Union[str, Path], dst: Union[str, Path], overwrite: bool = False) -> bool:
    """Safely copy a file."""
    try:
        src = Path(src)
        dst = Path(dst)
        if not src.exists():
            logger.error(f'Source file does not exist: {src}')
            return False
        if dst.exists() and not overwrite:
            logger.error(f'Destination file exists and overwrite=False: {dst}')
            return False
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return True
    except Exception as e:
        logger.exception(f'Error copying {src} to {dst}: {e}')
        return False

def safe_move(src: Union[str, Path], dst: Union[str, Path], overwrite: bool = False) -> bool:
    """Safely move a file or directory."""
    try:
        src = Path(src)
        dst = Path(dst)
        if not src.exists():
            logger.error(f'Source path does not exist: {src}')
            return False
        if dst.exists() and not overwrite:
            logger.error(f'Destination path exists and overwrite=False: {dst}')
            return False
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        return True
    except Exception as e:
        logger.exception(f'Error moving {src} to {dst}: {e}')
        return False

def rotate_file(path: Union[str, Path], max_size: int = 10 * 1024 * 1024, max_files: int = 5) -> None:
    """Rotate a file if it exceeds max_size."""
    path = Path(path)
    if not path.exists():
        raise FileOpsError(f'File not found: {path}')
    if path.stat().st_size < max_size:
        return
    for i in range(max_files - 1, 0, -1):
        older = path.with_suffix(f"{path.suffix}.{i - 1}" if i - 1 else path.suffix)
        newer = path.with_suffix(f"{path.suffix}.{i}")
        if older.exists():
            older.replace(newer)
    try:
        backup = path.with_suffix(f"{path.suffix}.1")
        try:
            path.replace(backup)
        except PermissionError:
            for _ in range(3):
                time.sleep(0.05)
                try:
                    path.replace(backup)
                    break
                except PermissionError:
                    continue
        if path.exists():
            try:
                path.unlink()
            except PermissionError:
                time.sleep(0.05)
                if path.exists():
                    path.unlink()
        path.write_text("")
    except Exception as e:
        raise FileOpsIOError(f'Failed to rotate file {path}: {e}')

def backup_file(path: Union[str, Path], backup_suffix: str = '.bak') -> Optional[Path]:
    """Create a backup of a file."""
    path = Path(path)
    if not path.exists():
        raise FileOpsError(f'File not found: {path}')
    backup_path = path.with_suffix(backup_suffix)
    try:
        shutil.copy2(path, backup_path)
        return backup_path
    except PermissionError as e:
        raise FileOpsPermissionError(f'Permission denied: {path}') from e
    except IOError as e:
        raise FileOpsIOError(f'I/O error: {path}') from e

def restore_backup(path: Union[str, Path], backup_suffix: str = '.bak') -> bool:
    """Restore a file from its backup."""
    path = Path(path)
    backup_path = path.with_suffix(backup_suffix)
    if not backup_path.exists():
        raise FileOpsError(f'Backup not found: {backup_path}')
    try:
        shutil.copy2(backup_path, path)
        return True
    except PermissionError as e:
        raise FileOpsPermissionError(f'Permission denied: {path}') from e
    except IOError as e:
        raise FileOpsIOError(f'I/O error: {path}') from e
