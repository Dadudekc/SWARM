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
    """Unified log handling system combining batching and reading functionality."""
    
    def __init__(self, config: LogConfig):
        """Initialize the log pipeline.
        
        Args:
            config: Log configuration
        """
        self.config = config
        self.batch: List[Dict[str, Any]] = []
        self.last_batch_time = time.time()
        self._running = False
        
        # Batching state
        self.entries = []
        self.last_batch_time = datetime.now()
        self._shutdown = False
        
        # Threading and locking
        self._lock = threading.RLock()
        self._file_locks = {}
        
        # Ensure log directory exists
        self.config.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Register cleanup
        atexit.register(self.stop)
    
    def _get_file_lock(self, platform: str) -> threading.RLock:
        """Get or create file lock for platform."""
        with self._lock:
            if platform not in self._file_locks:
                self._file_locks[platform] = threading.RLock()
            return self._file_locks[platform]
    
    def _is_file_locked(self, filepath: str) -> bool:
        """Check if a file is locked on Windows."""
        if platform.system() != 'Windows':
            return False
        try:
            filepath = str(filepath)
            GENERIC_READ = 0x80000000
            FILE_SHARE_READ = 0x00000001
            FILE_SHARE_DELETE = 0x00000004
            FILE_SHARE_WRITE = 0x00000002
            OPEN_EXISTING = 3
            INVALID_HANDLE_VALUE = -1
            
            handle = win32file.CreateFile(
                filepath,
                GENERIC_READ,
                FILE_SHARE_READ | FILE_SHARE_DELETE | FILE_SHARE_WRITE,
                None,
                OPEN_EXISTING,
                win32con.FILE_ATTRIBUTE_NORMAL,
                None
            )
            if handle == INVALID_HANDLE_VALUE:
                return True
            win32file.CloseHandle(handle)
            return False
        except Exception as e:
            logger.error(f"Error checking file lock for {filepath}: {e}")
            return True
    
    def _force_close_handle(self, filepath: str) -> None:
        """Force close any open handles to a file on Windows."""
        if platform.system() != 'Windows':
            return
        try:
            handle = win32file.CreateFile(
                str(filepath),
                win32con.GENERIC_READ | win32con.GENERIC_WRITE,
                0,
                None,
                win32con.OPEN_EXISTING,
                win32con.FILE_ATTRIBUTE_NORMAL | win32con.FILE_FLAG_DELETE_ON_CLOSE,
                None
            )
            win32file.CloseHandle(handle)
        except pywintypes.error as e:
            if e.winerror != 32:  # Not a sharing violation
                logger.warning(f"Error closing handle for {filepath}: {e}")
    
    def _wait_for_file_unlock(self, file_path: str) -> bool:
        """Wait for file to be unlocked with exponential backoff."""
        for attempt in range(self.config.max_retries):
            try:
                if platform.system() == 'Windows':
                    if not self._is_file_locked(file_path):
                        return True
                    self._force_close_handle(file_path)
                    time.sleep(0.2 + 0.1 * attempt)  # Exponential backoff
                    if not self._is_file_locked(file_path):
                        return True
                else:
                    with open(file_path, 'r'):
                        return True
            except (OSError, pywintypes.error) as e:
                logger.warning(f"Wait for unlock failed (attempt {attempt+1}) for {file_path}: {e}")
                time.sleep(0.2 + 0.1 * attempt)
        logger.error(f"File {file_path} could not be unlocked after {self.config.max_retries} attempts.")
        return False
    
    def add_entry(self, entry: Dict[str, Any]) -> None:
        """Add an entry to the batch.
        
        Args:
            entry: Log entry to add
        """
        try:
            # Validate required fields
            if "platform" not in entry:
                raise ValueError("Platform must be specified")
            if "message" not in entry:
                raise ValueError("Message must be specified")
            
            # Set defaults
            if "level" not in entry:
                entry["level"] = "INFO"
            if "timestamp" not in entry:
                entry["timestamp"] = datetime.now().isoformat()
            
            # Convert dict to LogEntry if needed
            if not isinstance(entry, LogEntry):
                entry = LogEntry.from_dict(entry)
            
            # Check if we need to flush
            current_time = time.time()
            if (current_time - self.last_batch_time >= self.config.batch_timeout or 
                len(self.batch) >= self.config.batch_size):
                self.flush()
            
            # Add to batch
            self.batch.append(entry.to_dict())
            
        except Exception as e:
            logger.error(f"Error adding entry to batch: {e}")
    
    def flush(self) -> None:
        """Flush the current batch to log files."""
        if not self.batch:
            return
            
        try:
            # Group entries by platform
            platform_entries: Dict[str, List[Dict[str, Any]]] = {}
            for entry in self.batch:
                platform = entry["platform"]
                if platform not in platform_entries:
                    platform_entries[platform] = []
                platform_entries[platform].append(entry)
            
            # Write to platform log files
            for platform, entries in platform_entries.items():
                log_file = self.config.get_platform_log(platform)
                if not log_file:
                    log_file = self.config.add_platform(platform)
                
                # Ensure file exists
                log_file.touch(exist_ok=True)
                
                # Write entries
                with open(log_file, 'a') as f:
                    for entry in entries:
                        f.write(json.dumps(entry) + '\n')
            
            # Clear batch and update time
            self.batch.clear()
            self.last_batch_time = time.time()
            
        except Exception as e:
            logger.error(f"Error flushing batch: {e}")
    
    def get_log_info(self) -> Dict[str, Any]:
        """Get information about log files.
        
        Returns:
            Dictionary with log file information
        """
        try:
            info = {
                "total_size": 0,
                "total_entries": 0,
                "platforms": {}
            }
            
            for platform, log_file in self.config.platforms.items():
                if log_file.exists():
                    size = log_file.stat().st_size
                    entries = len(self.read_logs(platform))
                    info["platforms"][platform] = {
                        "size_bytes": size,
                        "entries": entries
                    }
                    info["total_size"] += size
                    info["total_entries"] += entries
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting log info: {e}")
            return {
                "total_size": 0,
                "total_entries": 0,
                "platforms": {}
            }
    
    def read_logs(self, platform: str) -> List[Dict[str, Any]]:
        """Read logs for a platform.
        
        Args:
            platform: Platform name
            
        Returns:
            List of log entries
        """
        log_file = self.config.get_platform_log(platform)
        if not log_file or not log_file.exists():
            return []
            
        entries = []
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    entries.append(entry)
                except json.JSONDecodeError:
                    continue
        return entries
    
    def start(self) -> None:
        """Start the pipeline."""
        if self._running:
            raise RuntimeError("Pipeline is already running")
        self._running = True
    
    def stop(self) -> None:
        """Stop the pipeline."""
        if not self._running:
            raise RuntimeError("Pipeline is not running")
        self.flush()
        self._running = False
    
    def __del__(self):
        """Cleanup on deletion."""
        self.stop() 
