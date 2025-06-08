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
    
    def add_entry(self, entry: Union[LogEntry, Dict[str, Any]]) -> bool:
        """Add entry to batch.
        
        Args:
            entry: LogEntry or dict to add
            
        Returns:
            bool: True if successful
        """
        if self._shutdown:
            raise RuntimeError("LogPipeline is shut down")
            
        try:
            with self._lock:
                # Convert dict to LogEntry if needed
                if isinstance(entry, dict):
                    if "platform" not in entry:
                        raise ValueError("Entry dict must contain 'platform' field")
                    if "message" not in entry:
                        raise ValueError("Entry dict must contain 'message' field")
                    if "level" not in entry:
                        entry["level"] = "INFO"  # Default level
                    if "timestamp" not in entry:
                        entry["timestamp"] = datetime.now().isoformat()
                    entry = LogEntry.from_dict(entry)
                
                # Check if we should flush due to timeout
                if (datetime.now() - self.last_batch_time).total_seconds() >= self.batch_timeout:
                    self.flush()
                
                # Check if we're at batch size limit
                if len(self.entries) >= self.batch_size:
                    self.flush()  # Flush before adding new entry
                
                # Add to batch
                self.entries.append(entry)
                return True
                
        except Exception as e:
            logger.error(f"Error adding entry to batch: {str(e)}")
            return False
    
    def flush(self) -> bool:
        """Flush current batch to disk.
        
        Returns:
            bool: True if successful
        """
        if not self.entries:
            return True
            
        try:
            with self._lock:
                # Group entries by platform
                platform_entries = {}
                for entry in self.entries:
                    platform_entries.setdefault(entry.platform, []).append(entry)
                
                # Write each platform's entries
                for platform, entries in platform_entries.items():
                    with self._get_file_lock(platform):
                        log_file = Path(self.log_dir).resolve() / f"{platform}.json"
                        
                        # Read existing entries
                        existing_entries = []
                        if log_file.exists():
                            if not self._wait_for_file_unlock(log_file):
                                logger.warning(f"Could not unlock file {log_file}")
                                continue
                            try:
                                with open(log_file, 'r') as f:
                                    content = f.read()
                                    if content:
                                        existing_entries = json.loads(content)
                                        if not isinstance(existing_entries, list):
                                            existing_entries = [existing_entries]
                            except json.JSONDecodeError:
                                logger.error(f"Invalid JSON in log file {log_file}")
                                existing_entries = []
                        
                        # Add new entries
                        existing_entries.extend(entry.to_dict() for entry in entries)
                        
                        # Write back to file with atomic write
                        temp_file = log_file.with_suffix('.tmp')
                        try:
                            with open(temp_file, 'w') as f:
                                json.dump(existing_entries, f, indent=2)
                            temp_file.replace(log_file)
                        except Exception as e:
                            logger.error(f"Error writing log file {log_file}: {str(e)}")
                            if temp_file.exists():
                                temp_file.unlink()
                            raise
                
                # Clear batch
                self.entries = []
                self.last_batch_time = datetime.now()
                return True
                
        except Exception as e:
            logger.error(f"Error flushing batch: {str(e)}")
            return False
    
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
            Dict[str, Any]: Log file statistics
        """
        info = {
            "total_files": 0,
            "total_entries": 0,
            "platforms": {},
            "levels": {},
            "oldest_entry": None,
            "newest_entry": None
        }
        
        try:
            for log_file in self.log_dir.glob("*.json"):
                if not log_file.exists():
                    continue
                    
                if not self._wait_for_file_unlock(log_file):
                    continue
                    
                try:
                    with open(log_file, 'r') as f:
                        content = f.read()
                        if not content:
                            continue
                            
                        entries = json.loads(content)
                        if not isinstance(entries, list):
                            entries = [entries]
                            
                        for entry in entries:
                            platform = entry.get("platform", "unknown")
                            if platform not in info["platforms"]:
                                info["platforms"][platform] = 0
                            info["platforms"][platform] += 1
                            
                            level = entry.get("level", "unknown")
                            if level not in info["levels"]:
                                info["levels"][level] = 0
                            info["levels"][level] += 1
                            
                            timestamp = entry.get("timestamp")
                            if timestamp:
                                if not info["oldest_entry"] or timestamp < info["oldest_entry"]:
                                    info["oldest_entry"] = timestamp
                                if not info["newest_entry"] or timestamp > info["newest_entry"]:
                                    info["newest_entry"] = timestamp
                                    
                        info["total_entries"] += len(entries)
                        info["total_files"] += 1
                        
                except Exception as e:
                    logger.error(f"Error reading log file {log_file}: {e}")
                    continue
                    
            return info
            
        except Exception as e:
            logger.error(f"Error getting log info: {e}")
            return info
    
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
