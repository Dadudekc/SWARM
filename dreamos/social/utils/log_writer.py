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
            config: LogConfig instance containing writer configuration
        """
        self.config = config
        self._ensure_log_dir()
    
    def _ensure_log_dir(self) -> None:
        """Ensure log directory exists."""
        self.config.log_dir.mkdir(parents=True, exist_ok=True)
    
    def write_log(self, platform: str, message: str, level: str = "INFO") -> None:
        """Write a log entry.
        
        Args:
            platform: Platform name
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
        """Write a log entry in JSON format.
        
        Args:
            entry: Log entry dictionary
        """
        if "platform" not in entry:
            raise ValueError("Platform must be specified")
            
        platform = entry["platform"]
        log_file = self.config.platforms.get(platform)
        
        if not log_file:
            log_file = self.config.log_dir / f"{platform}.log"
            self.config.platforms[platform] = log_file
        
        # Ensure log file exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_file.touch(exist_ok=True)
        
        # Write entry
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    
    def read_logs(self, platform: str, level: Optional[str] = None) -> List[Dict[str, Any]]:
        """Read log entries for a platform.
        
        Args:
            platform: Platform name
            level: Optional log level to filter by
            
        Returns:
            List of log entries
        """
        entries = []
        log_file = self.config.platforms.get(platform)
        
        if not log_file or not log_file.exists():
            return entries
            
        try:
            with log_file.open("r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if level is None or entry.get("level") == level:
                            entries.append(entry)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"Error reading logs: {e}")
            
        return entries
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics about log files.
        
        Returns:
            Dictionary containing metrics
        """
        metrics = {
            "total_size": 0,
            "platforms": {},
            "total_entries": 0
        }
        
        try:
            for platform, log_file in self.config.platforms.items():
                if log_file.exists():
                    size = log_file.stat().st_size
                    metrics["total_size"] += size
                    
                    # Count entries
                    entry_count = 0
                    with log_file.open("r", encoding="utf-8") as f:
                        for _ in f:
                            entry_count += 1
                    
                    metrics["platforms"][platform] = {
                        "size": size,
                        "entries": entry_count
                    }
                    metrics["total_entries"] += entry_count
        except Exception as e:
            print(f"Error getting metrics: {e}")
        
        return metrics

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
