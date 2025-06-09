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
        """Initialize log pipeline.
        
        Args:
            log_dir: Log directory path or LogConfig object
        """
        if isinstance(log_dir, LogConfig):
            self._config = log_dir
            self.log_dir = log_dir.log_dir
            self.batch_size = log_dir.batch_size
            self.batch_timeout = log_dir.batch_timeout
        else:
            self._config = None
            self.log_dir = Path(log_dir)
            self.batch_size = 100
            self.batch_timeout = 5.0
            
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._writer = LogWriter(self.log_dir)
        self._batch: List[LogEntry] = []
        self._stop_event = threading.Event()
        self._flush_thread: Optional[threading.Thread] = None

    def add_entry(self, entry: Union[LogEntry, Dict]) -> bool:
        """Add a log entry to the batch.
        
        Args:
            entry: LogEntry or dict with entry data
            
        Returns:
            True if successful
        """
        if isinstance(entry, dict):
            if "message" not in entry:
                raise ValueError("Log entry must have a message field")
            entry = LogEntry.from_dict(entry)
            
        if not entry.message or not entry.level:
            return False
            
        self._batch.append(entry)
        
        if len(self._batch) >= self.batch_size:
            self.flush()
            
        return True

    def flush(self) -> bool:
        """Flush batched entries to log files.
        
        Returns:
            True if successful
        """
        if not self._batch:
            return True
            
        try:
            # Group entries by platform
            entries_by_platform: Dict[str, List[LogEntry]] = {}
            for entry in self._batch:
                platform = entry.platform
                if platform not in entries_by_platform:
                    entries_by_platform[platform] = []
                entries_by_platform[platform].append(entry)
                
            # Write entries for each platform
            for platform, entries in entries_by_platform.items():
                if not self._writer.write_log_json(entries):
                    logging.error(f"Error writing entries for platform {platform}")
                    return False
                    
            self._batch.clear()
            return True
            
        except Exception as e:
            logging.error(f"Error flushing entries: {e}")
            return False

    def get_log_info(self) -> Dict:
        """Get information about log files.
        
        Returns:
            Dictionary with log info
        """
        info = {
            "total_size": 0,
            "file_count": 0,
            "entry_count": 0,
            "platforms": {}
        }
        
        for log_file in self.log_dir.glob("*.log*"):
            try:
                size = log_file.stat().st_size
                info["total_size"] += size
                info["file_count"] += 1
                
                # Count entries in file
                with open(log_file) as f:
                    entry_count = sum(1 for _ in f)
                info["entry_count"] += entry_count
                
                # Add platform info
                platform = log_file.stem
                if platform not in info["platforms"]:
                    info["platforms"][platform] = {
                        "size": 0,
                        "entry_count": 0
                    }
                info["platforms"][platform]["size"] += size
                info["platforms"][platform]["entry_count"] += entry_count
                
            except Exception as e:
                logging.error(f"Error getting info for {log_file}: {e}")
                
        return info

    def read_logs(
        self,
        platform: Optional[str] = None,
        level: Optional[LogLevel] = None,
        limit: int = 100
    ) -> List[LogEntry]:
        """Read log entries.
        
        Args:
            platform: Optional platform filter
            level: Optional level filter
            limit: Maximum number of entries
            
        Returns:
            List of log entries
        """
        return self._writer.read_logs(platform, level, limit)

    def _flush_thread(self):
        """Background thread for periodic flushing."""
        while not self._stop_event.is_set():
            time.sleep(self.batch_timeout)
            if self._batch:
                self.flush()

    def start(self):
        """Start the log pipeline."""
        if self._flush_thread is not None:
            raise RuntimeError("Log pipeline is already running")
            
        self._stop_event.clear()
        self._flush_thread = threading.Thread(target=self._flush_thread, daemon=True)
        self._flush_thread.start()

    def stop(self):
        """Stop the log pipeline."""
        if self._flush_thread is None:
            raise RuntimeError("Log pipeline is not running")
            
        self._stop_event.set()
        self._flush_thread.join()
        self._flush_thread = None
        
        # Final flush
        self.flush()

    def __del__(self):
        """Cleanup on deletion."""
        self.stop() 
