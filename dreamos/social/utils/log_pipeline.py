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
    
    def __init__(
        self,
        log_dir: str,
        batch_size: int = 1000,
        batch_timeout: float = 5.0,
        max_retries: int = 10
    ):
        """Initialize log pipeline.
        
        Args:
            log_dir: Directory to write/read log files
            batch_size: Maximum number of entries per batch
            batch_timeout: Maximum time to wait before flushing (seconds)
            max_retries: Maximum number of retries for file operations
        """
        self.log_dir = Path(log_dir)
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.max_retries = max_retries
        
        # Batching state
        self.entries = []
        self.last_batch_time = datetime.now()
        self._shutdown = False
        
        # Threading and locking
        self._lock = threading.RLock()
        self._file_locks = {}
        
        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
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
        for attempt in range(self.max_retries):
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
        logger.error(f"File {file_path} could not be unlocked after {self.max_retries} attempts.")
        return False
    
    def add_entry(self, entry: Union[Dict[str, Any], LogEntry]) -> None:
        """Add a log entry to the batch.
        
        Args:
            entry: Log entry as dict or LogEntry object
        """
        try:
            # Convert dict to LogEntry if needed
            if isinstance(entry, dict):
                if "platform" not in entry:
                    raise ValueError("Platform must be specified")
                if "message" not in entry:
                    raise ValueError("Message must be specified")
                    
                # Set defaults if not provided
                if "level" not in entry:
                    entry["level"] = "INFO"
                if "timestamp" not in entry:
                    entry["timestamp"] = datetime.now()
                    
                entry = LogEntry(**entry)
                
            # Check if we need to flush
            if (datetime.now() - self.last_batch_time).total_seconds() >= self.batch_timeout:
                self.flush()
                
            # Add to batch
            self.entries.append(entry)
            
            # Flush if batch is full
            if len(self.entries) >= self.batch_size:
                self.flush()
                
        except Exception as e:
            logger.error(f"Error adding entry to batch: {e}")
            raise
    
    def flush(self) -> None:
        """Flush the current batch to log files."""
        if not self.entries:
            return
        
        try:
            # Group entries by platform
            platform_entries = {}
            for entry in self.entries:
                if entry.platform not in platform_entries:
                    platform_entries[entry.platform] = []
                platform_entries[entry.platform].append(entry)
                
            # Write entries for each platform
            for platform, entries in platform_entries.items():
                log_file = self.log_dir / f"{platform}.log"
                
                # Ensure log file exists
                log_file.parent.mkdir(exist_ok=True)
                if not log_file.exists():
                    log_file.touch()
                    
                # Write entries
                with open(log_file, "a") as f:
                    for entry in entries:
                        f.write(json.dumps(entry.to_dict()) + "\n")
                    
            # Clear batch and update last batch time
            self.entries.clear()
            self.last_batch_time = datetime.now()
            
        except Exception as e:
            logger.error(f"Error flushing log batch: {e}")
            raise
    
    def read_logs(
        self,
        platform: Optional[str] = None,
        level: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Read log entries with filtering.
        
        Args:
            platform: Optional platform to filter by
            level: Optional log level to filter by
            limit: Optional maximum number of entries to return
            
        Returns:
            List[Dict[str, Any]]: Filtered log entries
        """
        entries = []
        try:
            if platform:
                log_files = [self.log_dir / f"{platform}.json"]
            else:
                log_files = list(self.log_dir.glob("*.json"))
                
            for log_file in log_files:
                if not log_file.exists():
                    continue
                    
                if not self._wait_for_file_unlock(log_file):
                    logger.warning(f"Could not unlock file {log_file}")
                    continue
                    
                try:
                    with open(log_file, 'r') as f:
                        content = f.read()
                        if not content:
                            continue
                            
                        file_entries = json.loads(content)
                        if not isinstance(file_entries, list):
                            file_entries = [file_entries]
                            
                        for entry in file_entries:
                            if level and entry.get("level") != level:
                                continue
                            entries.append(entry)
                            if limit and len(entries) >= limit:
                                break
                                
                except Exception as e:
                    logger.error(f"Error reading log file {log_file}: {e}")
                    continue
                    
            # Sort by timestamp and apply limit
            entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            if limit:
                entries = entries[:limit]
                
            return entries
            
        except Exception as e:
            logger.error(f"Error reading logs: {e}")
            return []
    
    def get_log_info(self) -> Dict[str, Any]:
        """Get information about log files.
        
        Returns:
            Dict containing log file information
        """
        try:
            info = {
                "platforms": {},
                "total_size": 0,
                "total_entries": 0
            }
            
            # Get all log files
            log_dir = Path(self.log_dir)
            for log_file in log_dir.glob("*.log"):
                platform = log_file.stem
                size = log_file.stat().st_size
                
                # Count entries
                entry_count = 0
                with open(log_file) as f:
                    for _ in f:
                        entry_count += 1
                    
                info["platforms"][platform] = {
                    "size": size,
                    "entries": entry_count
                }
                info["total_size"] += size
                info["total_entries"] += entry_count
                
            return info
            
        except Exception as e:
            logger.error(f"Error getting log info: {e}")
            return {"platforms": {}, "total_size": 0, "total_entries": 0}
    
    def stop(self) -> None:
        """Stop pipeline and flush any remaining entries."""
        with self._lock:
            if not self._shutdown:
                self._shutdown = True
                self.flush()
                self._file_locks.clear()
    
    def __del__(self):
        """Cleanup on deletion."""
        self.stop() 
