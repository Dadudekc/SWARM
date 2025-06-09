"""
Log Writer Module
----------------
Handles writing log entries to files in various formats.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Union, TextIO
import json
from enum import Enum
from dataclasses import dataclass
import os
import logging
import tempfile
from contextlib import contextmanager
import platform as platform_module  # Rename to avoid conflict
import threading
import portalocker
import stat
import shutil
import time
import atexit
from datetime import timedelta

from .log_entry import LogEntry
from dreamos.core.logging.log_config import LogConfig, LogLevel
from dreamos.core.config.config_manager import ConfigManager
from dreamos.core.log_manager import LogConfig as SocialLogConfig, LogLevel as SocialLogLevel
from dreamos.core.monitoring.metrics import LogMetrics

__all__ = [
    'LogLevel',
    'LogWriter',
    '_ensure_log_dir',
    '_cleanup_all_locks',
    '_get_file_lock',
    'write_log',
    'write_log_json',
    'read_logs',
    'cleanup_old_logs',
    'record_metric',
    'get_metrics',
    'get_summary',
    'save_metrics',
    'load_metrics',
    'clear_metrics',
    'write_json_log'
]

logger = logging.getLogger(__name__)

# Import appropriate locking mechanism based on platform
if platform_module.system() == 'Windows':
    import msvcrt
    import win32file
    import win32con
    import win32api
    import pywintypes
    LOCK_EX = win32con.LOCKFILE_EXCLUSIVE_LOCK
    LOCK_SH = 0  # Shared lock not used
    LOCK_NB = win32con.LOCKFILE_FAIL_IMMEDIATELY
    LOCK_UN = 0  # Unlock not needed, handled by closing file
    
    # Try to import win32security, but don't fail if not available
    try:
        import win32security
        import ntsecuritycon as con
        HAS_WIN32SECURITY = True
    except ImportError:
        logger.warning("win32security not available, will use basic Windows permissions")
        HAS_WIN32SECURITY = False
else:
    import fcntl
    LOCK_EX = fcntl.LOCK_EX
    LOCK_SH = fcntl.LOCK_SH
    LOCK_NB = fcntl.LOCK_NB
    LOCK_UN = fcntl.LOCK_UN
    HAS_WIN32SECURITY = False

class LogLevel(Enum):
    """Log levels for entries."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogWriter:
    """Handles writing log entries to files."""
    
    def __init__(self, log_dir: Union[str, Path, LogConfig]):
        """Initialize log writer.
        
        Args:
            log_dir: Log directory path or LogConfig object
        """
        if isinstance(log_dir, LogConfig):
            self._config = log_dir
            self.log_dir = log_dir.log_dir
        else:
            self._config = None
            self.log_dir = Path(log_dir)
            
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._file_locks: Dict[str, logging.FileHandler] = {}

    def write_log(self, entry: Union[LogEntry, Dict], platform: Optional[str] = None) -> bool:
        """Write a log entry.
        
        Args:
            entry: LogEntry or dict with entry data
            platform: Optional platform name
            
        Returns:
            True if successful
        """
        if isinstance(entry, dict):
            entry = LogEntry.from_dict(entry)
            
        if not entry.message or not entry.level:
            return False
            
        log_file = self._get_log_file(platform)
        with self._get_file_lock(log_file) as handler:
            handler.write(f"{entry}\n")
            handler.flush()
        return True

    def write_log_json(self, entries: Union[LogEntry, Dict, List[Union[LogEntry, Dict]]]) -> bool:
        """Write log entries in JSON format.
        
        Args:
            entries: Single entry or list of entries
            
        Returns:
            True if successful
        """
        if not isinstance(entries, list):
            entries = [entries]
            
        for entry in entries:
            if isinstance(entry, dict):
                entry = LogEntry.from_dict(entry)
            if not self.write_log(entry):
                return False
        return True

    def read_logs(self, platform: Optional[str] = None, level: Optional[LogLevel] = None, limit: int = 100) -> List[LogEntry]:
        """Read log entries.
        
        Args:
            platform: Optional platform filter
            level: Optional level filter
            limit: Maximum number of entries
            
        Returns:
            List of log entries
        """
        log_file = self._get_log_file(platform)
        if not log_file.exists():
            return []
            
        entries = []
        with open(log_file, 'r') as f:
            for line in f:
                if len(entries) >= limit:
                    break
                try:
                    entry = LogEntry.from_dict(json.loads(line))
                    if level is None or entry.level == level:
                        entries.append(entry)
                except (json.JSONDecodeError, ValueError):
                    continue
        return entries

    def cleanup_old_logs(self, days: int = 30) -> int:
        """Remove log files older than specified days.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of files removed
        """
        count = 0
        for log_file in self.log_dir.glob("*.log*"):
            if log_file.stat().st_mtime < (time.time() - days * 86400):
                try:
                    log_file.unlink()
                    count += 1
                except OSError:
                    continue
        return count

    def _get_log_file(self, platform: Optional[str] = None) -> Path:
        """Get log file path for platform.
        
        Args:
            platform: Optional platform name
            
        Returns:
            Log file path
        """
        if platform and self._config and platform in self._config.platforms:
            return self._config.platforms[platform]
        return self.log_dir / "social.log"

    def _get_file_lock(self, log_file: Path) -> logging.FileHandler:
        """Get file lock for log file.
        
        Args:
            log_file: Log file path
            
        Returns:
            File handler
        """
        if str(log_file) not in self._file_locks:
            handler = logging.FileHandler(log_file)
            handler.setFormatter(logging.Formatter(self._config.format if self._config else "%(message)s"))
            self._file_locks[str(log_file)] = handler
        return self._file_locks[str(log_file)]

    def cleanup_all_locks(self):
        """Clean up all file locks."""
        for handler in self._file_locks.values():
            handler.close()
        self._file_locks.clear()

    def record_metric(self, name: str, value: float, tags: Optional[Dict] = None, metadata: Optional[Dict] = None):
        """Record a metric (no-op for backward compatibility)."""
        pass

def write_json_log(platform: str, status: str, message: str, level: str = "INFO", 
                  tags: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None,
                  error: Optional[str] = None) -> None:
    """Write a JSON log entry.
    
    Args:
        platform: Platform name
        status: Status of the operation
        message: Log message
        level: Log level (default: INFO)
        tags: Optional list of tags
        metadata: Optional metadata dictionary
        error: Optional error message
    """
    writer = LogWriter(str(Path.cwd() / "logs"))
    entry = LogEntry(
        platform=platform,
        status=status,
        message=message,
        level=level,
        tags=tags,
        metadata=metadata,
        error=error
    )
    writer.write_log(entry) 
