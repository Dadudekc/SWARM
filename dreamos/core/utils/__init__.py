"""
Core Utilities

Provides shared utility functions and classes for the Dream.OS system.
"""

from .coordinate_utils import (
    transform_coordinates,
    load_coordinates,
    validate_coordinates,
    save_coordinates
)

from .retry_utils import (
    retry,
    with_retry,
    calculate_retry_delay
)

from .file_utils import (
    ensure_dir,
    safe_write,
    safe_read,
    load_json,
    save_json,
    read_yaml,
    write_yaml,
    atomic_write,
    backup_file,
    restore_backup,
    safe_file_handle,
    safe_rmdir,
    rotate_file,
    find_files,
    cleanup_old_files,
    load_yaml,
    save_yaml
)

__all__ = [
    # Coordinate utilities
    'transform_coordinates',
    'load_coordinates',
    'validate_coordinates',
    'save_coordinates',
    
    # Retry utilities
    'retry',
    'with_retry',
    'calculate_retry_delay',
    
    # File utilities
    'ensure_dir',
    'safe_write',
    'safe_read',
    'load_json',
    'save_json',
    'read_yaml',
    'write_yaml',
    'atomic_write',
    'backup_file',
    'restore_backup',
    'safe_file_handle',
    'safe_rmdir',
    'rotate_file',
    'find_files',
    'cleanup_old_files',
    'load_yaml',
    'save_yaml'
]
