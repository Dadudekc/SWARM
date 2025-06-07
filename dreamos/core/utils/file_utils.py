"""Aggregate helpers for backward compatibility."""

from .safe_io import (
    atomic_write,
    safe_read,
    safe_write,
    async_atomic_write,
    async_delete_file,
)

from .serialization import (
    load_json,
    save_json,
    read_json,
    write_json,
    restore_backup,
    read_yaml,
    load_yaml,
    write_yaml,
    save_yaml,
    async_save_json,
    async_load_json,
)

from .file_ops import (
    ensure_dir,
    clear_dir,
    archive_file,
    extract_agent_id,
    backup_file,
    safe_rmdir,
    cleanup_old_files,
)

__all__ = [
    "atomic_write",
    "safe_read",
    "safe_write",
    "async_atomic_write",
    "async_delete_file",
    "load_json",
    "save_json",
    "read_json",
    "write_json",
    "restore_backup",
    "read_yaml",
    "load_yaml",
    "write_yaml",
    "save_yaml",
    "async_save_json",
    "async_load_json",
    "ensure_dir",
    "clear_dir",
    "archive_file",
    "extract_agent_id",
    "backup_file",
    "safe_rmdir",
    "cleanup_old_files",
]
