"""
Dream.OS Utilities Package

Utility functions for the Dream.OS system.

This package provides essential utilities used throughout the Dream.OS system.
It includes helpers for file operations, serialization, logging, and more.

Key modules:
    - json_utils: JSON serialization and validation
    - safe_io: Thread-safe file operations
    - serialization: Object serialization and deserialization
    - yaml_utils: YAML configuration handling
    - file_utils: File system operations
    - logging_utils: Logging configuration and helpers
    - core_utils: Core utility functions
    - agent_helpers: Agent-specific utilities
    - message_processor: Message processing utilities
    - retry: Retry mechanism for operations
    - system_ops: System operation utilities
    - region_finder: Region detection utilities
    - exceptions: Custom exceptions
"""

from . import (
    agent_helpers,
    agent_status,
    core_utils,
    exceptions,
    file_ops,
    file_utils,
    json_utils,
    logging_utils,
    message_processor,
    region_finder,
    retry,
    safe_io,
    serialization,
    system_ops,
    test_helpers,
    yaml_utils
)

# Re-export commonly used functions and classes
from .json_utils import (
    load_json,
    save_json,
    validate_json,
    JsonValidationError
)

from .safe_io import (
    safe_read,
    safe_write,
    SafeIOError
)

from .serialization import (
    serialize,
    deserialize,
    SerializationError
)

from .yaml_utils import (
    load_yaml,
    save_yaml,
    YamlError
)

from .file_utils import (
    ensure_dir,
    clean_dir,
    get_file_info,
    FileError
)

from .logging_utils import (
    setup_logging,
    get_logger,
    LogConfig
)

from .core_utils import (
    get_timestamp,
    format_duration,
    is_valid_uuid
)

from .agent_helpers import (
    get_agent_status
)

from .region_finder import (
    find_region
)

from .exceptions import (
    DreamOSError
)

__all__ = [
    # Module names
    'agent_helpers',
    'agent_status',
    'core_utils',
    'exceptions',
    'file_ops',
    'file_utils',
    'json_utils',
    'logging_utils',
    'message_processor',
    'region_finder',
    'retry',
    'safe_io',
    'serialization',
    'system_ops',
    'test_helpers',
    'yaml_utils',
    
    # Re-exported functions and classes
    'load_json',
    'save_json',
    'validate_json',
    'JsonValidationError',
    'safe_read',
    'safe_write',
    'SafeIOError',
    'serialize',
    'deserialize',
    'SerializationError',
    'load_yaml',
    'save_yaml',
    'YamlError',
    'ensure_dir',
    'clean_dir',
    'get_file_info',
    'FileError',
    'setup_logging',
    'get_logger',
    'LogConfig',
    'get_timestamp',
    'format_duration',
    'is_valid_uuid',
    'get_agent_status',
    'find_region',
    'DreamOSError'
]
