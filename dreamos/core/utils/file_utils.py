"""File utility aggregator."""

from .exceptions import (
    FileOpsError,
    FileOpsPermissionError,
    FileOpsIOError,
)
from .safe_io import (
    safe_file_handle,
    atomic_write,
    safe_write,
    safe_read,
)
from .serialization import (
    load_json,
    save_json,
    load_yaml,
    save_yaml,
    read_json,
    write_json,
    read_yaml,
    write_yaml,
)
from .file_ops import (
    ensure_dir,
    cleanup_old_files,
    find_files,
    safe_rmdir,
    safe_mkdir,
    safe_remove,
    safe_copy,
    safe_move,
    rotate_file,
    backup_file,
    restore_backup,
)

__all__ = [
    'FileOpsError',
    'FileOpsPermissionError',
    'FileOpsIOError',
    'safe_file_handle',
    'atomic_write',
    'safe_write',
    'safe_read',
    'load_json',
    'save_json',
    'load_yaml',
    'save_yaml',
    'read_json',
    'write_json',
    'read_yaml',
    'write_yaml',
    'ensure_dir',
    'cleanup_old_files',
    'find_files',
    'safe_rmdir',
    'safe_mkdir',
    'safe_remove',
    'safe_copy',
    'safe_move',
    'rotate_file',
    'backup_file',
    'restore_backup',
]
