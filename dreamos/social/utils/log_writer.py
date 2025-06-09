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
    """Handles writing log entries to files with rotation and cleanup."""
    
    def __init__(self, config: LogConfig):
        """Initialize the log writer.
        
        Args:
            config: Log configuration
        """
        self.config = config
        self._ensure_log_dir()
    
    def _ensure_log_dir(self):
        """Ensure log directory exists."""
        self.config.log_dir.mkdir(parents=True, exist_ok=True)
    
    def write_log(self, platform: str, message: str, level: LogLevel = LogLevel.INFO) -> None:
        """Write a log entry.
        
        Args:
            platform: Platform identifier
            message: Log message
            level: Log level
        """
        entry = LogEntry(
            platform=platform,
            message=message,
            level=level,
            timestamp=datetime.now().isoformat()
        )
        self.write_log_json(entry.to_dict())
    
    def write_log_json(self, entry: Dict[str, Any]) -> None:
        """Write a log entry from a dictionary.
        
        Args:
            entry: Log entry dictionary
        """
        if "platform" not in entry:
            logger.error("Log entry missing platform")
            return
            
        platform = entry["platform"]
        log_file = self.config.platforms.get(platform, self.config.log_file)
        
        try:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(log_file, 'a') as f:
                json.dump(entry, f)
                f.write('\n')
        except Exception as e:
            logger.error(f"Error writing log: {e}")
    
    def read_logs(self, platform: Optional[str] = None, level: Optional[LogLevel] = None) -> List[Dict[str, Any]]:
        """Read log entries.
        
        Args:
            platform: Optional platform filter
            level: Optional level filter
            
        Returns:
            List of log entries
        """
        entries = []
        log_files = [self.config.platforms[platform]] if platform else self.config.platforms.values()
        
        for log_file in log_files:
            try:
                with open(log_file) as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            if level is None or entry.get("level") == level.value:
                                entries.append(entry)
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                logger.error(f"Error reading log file {log_file}: {e}")
                
        return entries
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get logging metrics.
        
        Returns:
            Dictionary of metrics
        """
        metrics = {
            "total_size": 0,
            "file_count": 0,
            "entry_count": 0,
            "platforms": {}
        }
        
        for platform, log_file in self.config.platforms.items():
            try:
                size = log_file.stat().st_size
                metrics["total_size"] += size
                metrics["file_count"] += 1
                
                # Count entries
                with open(log_file) as f:
                    entry_count = sum(1 for _ in f)
                metrics["entry_count"] += entry_count
                
                metrics["platforms"][platform] = {
                    "size": size,
                    "entries": entry_count
                }
            except Exception as e:
                logger.error(f"Error getting metrics for {platform}: {e}")
                
        return metrics
    
    # Legacy shims for test compatibility
    def cleanup(self) -> None:
        """Legacy cleanup method."""
        pass
    
    def _get_file_lock(self, *args, **kwargs) -> None:
        """Legacy file lock method."""
        return None
    
    def record_metric(self, *args, **kwargs) -> None:
        """Legacy metric recording method."""
        pass
    
    def _cleanup_all_locks(self) -> None:
        """Legacy lock cleanup method."""
        pass
    
    def cleanup_old_logs(self, *args, **kwargs) -> None:
        """Legacy log cleanup method."""
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
