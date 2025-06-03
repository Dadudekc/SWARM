"""
Log Batcher Module
-----------------
Handles batching of log entries for efficient writing.
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import json
import os
import threading
import time
import logging
import portalocker
import tempfile
from pathlib import Path
import platform
import stat
import atexit
import shutil
import contextlib
import win32file
import win32con
import pywintypes

from .log_entry import LogEntry
from .log_rotator import LogRotator

logger = logging.getLogger(__name__)

class LogBatcher:
    """Batches log entries for efficient writing."""
    
    def __init__(self, batch_size: int, batch_timeout: float, log_dir: str):
        """Initialize batcher.
        
        Args:
            batch_size: Maximum number of entries per batch
            batch_timeout: Maximum time to wait before flushing (seconds)
            log_dir: Directory to write log files
        """
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.log_dir = Path(log_dir)
        self.entries = []
        self.last_batch_time = datetime.now()
        self._lock = threading.RLock()
        self._file_locks = {}
        self._shutdown = False
        
        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_file_lock(self, platform: str) -> threading.RLock:
        """Get or create file lock for platform.
        
        Args:
            platform: Platform name
            
        Returns:
            RLock: File lock for platform
        """
        with self._lock:
            if platform not in self._file_locks:
                self._file_locks[platform] = threading.RLock()
            return self._file_locks[platform]
    
    def add_entry(self, entry: Union[LogEntry, Dict[str, Any]]) -> bool:
        """Add entry to batch.
        
        Args:
            entry: LogEntry or dict to add
            
        Returns:
            bool: True if successful
        """
        if self._shutdown:
            raise RuntimeError("LogBatcher is shut down")
            
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
    
    def get_entries(self) -> List[LogEntry]:
        """Get entries from current batch.
        
        Returns:
            List[LogEntry]: Up to batch_size entries from current batch, removing them from the batch
        """
        with self._lock:
            if not self.entries:
                return []
            
            # Get entries up to batch_size and remove them from the batch
            entries = self.entries[:self.batch_size]
            self.entries = self.entries[self.batch_size:]
            self.last_batch_time = datetime.now()  # Update last batch time
            return entries
    
    def clear(self) -> None:
        """Clear current batch."""
        with self._lock:
            self.entries = []
            self.last_batch_time = datetime.now()
    
    def is_empty(self) -> bool:
        """Check if batch is empty.
        
        Returns:
            bool: True if batch is empty
        """
        with self._lock:
            return len(self.entries) == 0
    
    def stop(self) -> None:
        """Stop batcher and flush any remaining entries."""
        with self._lock:
            if not self._shutdown:
                self._shutdown = True
                self.flush()
                self._file_locks.clear()
    
    def __del__(self):
        """Cleanup on deletion."""
        self.stop()
    
    def _cleanup_all_locks(self):
        """Clean up all file locks."""
        for file_path, lock_info in list(self._file_locks.items()):
            try:
                if 'file' in lock_info:
                    portalocker.unlock(lock_info['file'])
                    lock_info['file'].close()
                if 'lock_file' in lock_info and lock_info['lock_file'].exists():
                    if platform.system() == 'Windows':
                        os.chmod(str(lock_info['lock_file']), stat.S_IWRITE | stat.S_IREAD)
                    else:
                        os.chmod(str(lock_info['lock_file']), 0o666)
                    lock_info['lock_file'].unlink()
            except Exception as e:
                logger.error(f"Failed to cleanup lock for {file_path}: {str(e)}")
            finally:
                self._file_locks.pop(file_path, None) 