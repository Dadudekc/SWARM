"""
Core Utilities
--------------
Core utility modules for Dream.OS.
"""

from .file_utils import (
    atomic_write,
    safe_read,
    load_json,
    save_json,
    ensure_dir,
    clear_dir,
    archive_file,
    extract_agent_id
)

from .system_ops import (
    with_retry,
    transform_coordinates,
    normalize_coordinates
)

from .logging_utils import (
    configure_logging,
    get_logger,
    log_platform_event
)

from .test_helpers import (
    load_test_config,
    setup_test_env,
    cleanup_test_env,
    mock_logger
)

__all__ = [
    # File operations
    "atomic_write",
    "safe_read",
    "load_json",
    "save_json",
    "ensure_dir",
    "clear_dir",
    "archive_file",
    "extract_agent_id",
    
    # System operations
    "with_retry",
    "transform_coordinates",
    "normalize_coordinates",
    
    # Logging
    "configure_logging",
    "get_logger",
    "log_platform_event",
    
    # Test helpers
    "load_test_config",
    "setup_test_env",
    "cleanup_test_env",
    "mock_logger"
]
