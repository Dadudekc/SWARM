"""
Log Types Module
---------------
Shared types and constants for logging system.
"""

from dataclasses import dataclass
from typing import Optional

# Constants
DEFAULT_MAX_SIZE_MB = 10
DEFAULT_MAX_FILES = 5
DEFAULT_MAX_AGE_DAYS = 30
DEFAULT_COMPRESS_AFTER_DAYS = 7
DEFAULT_MAX_BYTES = 10485760  # 10 MB in bytes

@dataclass
class RotationConfig:
    """Configuration for log rotation.
    
    Attributes:
        max_size_mb: Maximum size of log file in MB before rotation
        max_files: Maximum number of backup files to keep
        max_age_days: Maximum age of log files in days
        compress_after_days: Number of days after which to compress old logs
        backup_dir: Optional directory for backup files
        max_bytes: Maximum size of log file in bytes before rotation
    """
    max_size_mb: int = DEFAULT_MAX_SIZE_MB
    max_files: int = DEFAULT_MAX_FILES
    max_age_days: int = DEFAULT_MAX_AGE_DAYS
    compress_after_days: int = DEFAULT_COMPRESS_AFTER_DAYS
    backup_dir: Optional[str] = None
    max_bytes: int = DEFAULT_MAX_BYTES 
