import os
import logging
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger(__name__)

@contextmanager
def safe_file_handle(file_path: Union[str, Path], mode: str = 'r'):
    """Safely handle file operations with proper cleanup."""
    file_path = Path(file_path)
    temp_path = None
    try:
        if 'w' in mode or 'a' in mode:
            temp_path = tempfile.NamedTemporaryFile(delete=False)
            temp_path.close()
            yield temp_path.name
            shutil.move(temp_path.name, str(file_path))
        else:
            with open(file_path, mode) as f:
                yield f
    finally:
        if temp_path and os.path.exists(temp_path.name):
            try:
                os.unlink(temp_path.name)
            except Exception as e:
                logger.warning(f'Failed to cleanup temp file: {e}')

@contextmanager
def atomic_write(file_path: Union[str, Path], mode: str = 'w', encoding: str = 'utf-8'):
    """Atomically write to a file using a temporary file."""
    file_path = Path(file_path)
    temp_path = None
    try:
        temp_path = tempfile.NamedTemporaryFile(delete=False, mode=mode, encoding=encoding)
        yield temp_path
        temp_path.close()
        shutil.move(temp_path.name, str(file_path))
    finally:
        if temp_path and os.path.exists(temp_path.name):
            try:
                os.unlink(temp_path.name)
            except Exception as e:
                logger.warning(f'Failed to cleanup temp file: {e}')

def safe_write(file_path: Union[str, Path], content: str, encoding: str = 'utf-8') -> bool:
    """Safely write content to a file."""
    file_path = Path(file_path)
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with safe_file_handle(file_path, 'w') as f:
            with open(f, 'w', encoding=encoding) as fp:
                fp.write(content)
        return True
    except Exception as e:
        logger.error(f'Failed to write file {file_path}: {e}')
        return False

def safe_read(file_path: Union[str, Path], encoding: str = 'utf-8') -> Optional[str]:
    """Safely read content from a file."""
    file_path = Path(file_path)
    try:
        with safe_file_handle(file_path, 'r') as f:
            with open(f, 'r', encoding=encoding) as fp:
                return fp.read()
    except Exception as e:
        logger.error(f'Failed to read file {file_path}: {e}')
        return None
