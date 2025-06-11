"""
Log Pipeline Module
------------------
Unified log handling system that combines batching and reading functionality.
"""

import os
import json
import logging
import platform
import threading
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import portalocker
import tempfile
import atexit
import shutil
import contextlib
try:
    import win32file
    import win32con
    import pywintypes
except Exception:  # pragma: no cover - unavailable on non-Windows
    win32file = None
    win32con = None
    pywintypes = None

from .log_entry import LogEntry
from .log_rotator import LogRotator
from .log_config import LogConfig
from .log_level import LogLevel
from .log_writer import LogWriter

__all__ = [
    'LogPipeline',
    '_get_file_lock',
    '_is_file_locked',
    '_force_close_handle',
    '_wait_for_file_unlock',
    'add_entry',
    'flush',
    'read_logs',
    'get_log_info',
    'stop',
    '__del__'
]

logger = logging.getLogger(__name__)

class LogPipeline:
    """Handles batched log entry processing."""
    
    def __init__(self, log_dir: Union[str, Path, LogConfig]):
        """Initialize the log pipeline.
        
        Args:
            log_dir: Either a LogConfig object or path to log directory
        """
        if isinstance(log_dir, (str, Path)):
            self.config = LogConfig(log_dir=str(log_dir))
            self.log_dir = str(log_dir)  # Legacy compatibility
        else:
            self.config = log_dir
            self.log_dir = log_dir.log_dir  # Legacy compatibility
            
        self._writer = LogWriter(self.config)
        self._batch: List[LogEntry] = []
        self._lock = threading.Lock()
        self._running = False
        self._shutdown = False
        self._flush_thread: Optional[threading.Thread] = None
        self._logger = logging.getLogger(__name__)
        
        # Register cleanup on exit
        atexit.register(self.stop)

    def add_entry(self, entry: Union[LogEntry, Dict[str, Any]]) -> None:
        """Add a log entry to the batch.
        
        Args:
            entry: Either a LogEntry object or dict with entry data
        """
        if not self._running:
            self.start()
            
        # Convert dict to LogEntry if needed
        if isinstance(entry, dict):
            entry = LogEntry.from_dict(entry)
            
        with self._lock:
            self._batch.append(entry)
            if len(self._batch) >= self.config.batch_size:
                self.flush()

    def flush(self) -> None:
        """Flush the current batch to disk."""
        with self._lock:
            if not self._batch:
                return
                
            try:
                batch = self._batch.copy()
                self._batch.clear()
                
                # Group entries by platform
                entries_by_platform = {}
                for entry in batch:
                    platform = entry.platform
                    if platform not in entries_by_platform:
                        entries_by_platform[platform] = []
                    entries_by_platform[platform].append(entry)
                
                # Write entries for each platform
                for platform, entries in entries_by_platform.items():
                    log_file = os.path.join(self.config.log_dir, f"{platform}.log")
                    with self._writer._get_file_lock(log_file) as handler:
                        for entry in entries:
                            self._writer.write_log(entry, handler)
            except Exception as e:
                self._logger.error(f"Error flushing entries: {e}")

    def start(self) -> None:
        """Start the pipeline."""
        if self._running:
            return
            
        self._running = True
        self._shutdown = False
        self._flush_thread = threading.Thread(target=self._flush_thread_func, daemon=True)
        self._flush_thread.start()

    def stop(self) -> None:
        """Stop the pipeline."""
        if not self._running:
            return
            
        self._running = False
        self._shutdown = True
        if self._flush_thread:
            self._flush_thread.join(timeout=5.0)
        self.flush()

    def _flush_thread_func(self) -> None:
        """Background thread for periodic flushing."""
        while self._running and not self._shutdown:
            self.flush()
            time.sleep(self.config.batch_timeout)

    def get_log_info(self) -> Dict[str, Any]:
        """Get information about the log files."""
        info = {
            "platforms": {},
            "total_entries": 0,
            "total_size": 0
        }
        
        try:
            for platform in self.config.platforms:
                log_file = os.path.join(self.config.log_dir, f"{platform}.log")
                if os.path.exists(log_file):
                    size = os.path.getsize(log_file)
                    entries = len(self._writer.read_logs(log_file))
                    info["platforms"][platform] = {
                        "size": size,
                        "entries": entries
                    }
                    info["total_entries"] += entries
                    info["total_size"] += size
        except Exception as e:
            self._logger.error(f"Error getting log info: {e}")
            
        return info

    def read_logs(self, platform: Optional[str] = None, level: Optional[LogLevel] = None, limit: Optional[int] = None) -> List[LogEntry]:
        """Read logs from the specified platform."""
        try:
            if platform:
                log_file = os.path.join(self.config.log_dir, f"{platform}.log")
                return self._writer.read_logs(log_file, level, limit)
            else:
                all_logs = []
                for platform in self.config.platforms:
                    log_file = os.path.join(self.config.log_dir, f"{platform}.log")
                    logs = self._writer.read_logs(log_file, level, limit)
                    all_logs.extend(logs)
                return all_logs
        except Exception as e:
            self._logger.error(f"Error reading logs: {e}")
            return []

    def cleanup_old_logs(self, max_age_days: int = 30) -> None:
        """Legacy compatibility method."""
        self._writer.cleanup_old_logs(max_age_days)

    def _cleanup_all_locks(self) -> None:
        """Legacy compatibility method."""
        self._writer.cleanup()

    def __del__(self):
        """Cleanup on deletion."""
        self.stop() 
