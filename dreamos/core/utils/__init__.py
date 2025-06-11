"""
Utility functions and classes used throughout Dream.OS.
"""

from dreamos.core.utils.file_ops import (
    safe_mkdir,
    ensure_dir,
    clear_dir,
    archive_file,
    extract_agent_id,
    backup_file,
    safe_rmdir
)

from dreamos.core.utils.json_utils import (
    load_json,
    save_json,
    validate_json
)

from dreamos.core.utils.yaml_utils import (
    load_yaml,
    save_yaml,
    validate_yaml
)

from dreamos.core.utils.safe_io import (
    atomic_write,
    safe_read
)

from dreamos.core.utils.logging_utils import (
    get_logger,
    setup_logging
)

from dreamos.core.utils.core_utils import (
    get_timestamp,
    format_timestamp,
    generate_id
)

from dreamos.core.utils.exceptions import (
    FileOpsError,
    FileOpsPermissionError,
    FileOpsIOError
)

__all__ = [
    # File Operations
    'safe_mkdir',
    'ensure_dir',
    'clear_dir',
    'archive_file',
    'extract_agent_id',
    'backup_file',
    'safe_rmdir',
    
    # JSON Operations
    'load_json',
    'save_json',
    'validate_json',
    
    # YAML Operations
    'load_yaml',
    'save_yaml',
    'validate_yaml',
    
    # Safe I/O
    'atomic_write',
    'safe_read',
    
    # Logging
    'get_logger',
    'setup_logging',
    
    # Core Utilities
    'get_timestamp',
    'format_timestamp',
    'generate_id',
    
    # Exceptions
    'FileOpsError',
    'FileOpsPermissionError',
    'FileOpsIOError'
]
