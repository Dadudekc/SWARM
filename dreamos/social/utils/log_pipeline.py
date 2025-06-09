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
    """Pipeline for handling log entries with batching and platform-specific routing."""
    
    def __init__(self, config: LogConfig):
        """Initialize the pipeline.
        
        Args:
            config: Log configuration
        """
        self.config = config
        self.batch: List[LogEntry] = []
        self.running = False
        self._lock = threading.Lock()
        self._flush_thread = None
        
        # Ensure log directory exists
        self.config.log_dir.mkdir(parents=True, exist_ok=True)
    
    def add_entry(self, entry: Union[Dict[str, Any], LogEntry]) -> None:
        """Add a log entry to the pipeline.
        
        Args:
            entry: Log entry dictionary or LogEntry object
        """
        if not self.running:
            logger.warning("Pipeline not running, entry not added")
            return
            
        if isinstance(entry, dict):
            # Validate required fields
            if "platform" not in entry or "message" not in entry:
                logger.error("Log entry missing required fields")
                return
                
            # Set defaults
            entry.setdefault("level", LogLevel.INFO.value)
            entry.setdefault("timestamp", datetime.now().isoformat())
            
            # Convert to LogEntry
            entry = LogEntry(**entry)
            
        with self._lock:
            self.batch.append(entry)
            
            # Flush if batch size reached
            if len(self.batch) >= self.config.batch_size:
                self.flush()
    
    def flush(self) -> None:
        """Flush the current batch of log entries."""
        if not self.batch:
            return
            
        with self._lock:
            # Group entries by platform
            platform_entries: Dict[str, List[LogEntry]] = {}
            for entry in self.batch:
                platform = entry.platform
                if platform not in platform_entries:
                    platform_entries[platform] = []
                platform_entries[platform].append(entry)
            
            # Write entries to platform-specific files
            for platform, entries in platform_entries.items():
                log_file = self.config.platforms.get(platform, self.config.log_file)
                
                try:
                    log_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(log_file, 'a') as f:
                        for entry in entries:
                            json.dump(entry.to_dict(), f)
                            f.write('\n')
                except Exception as e:
                    logger.error(f"Error writing to {platform} log: {e}")
            
            # Clear batch
            self.batch.clear()
    
    def get_log_info(self) -> Dict[str, Any]:
        """Get information about log files.
        
        Returns:
            Dictionary containing log file information
        """
        info = {
            "total_size": 0,
            "platforms": {}
        }
        
        for platform, log_file in self.config.platforms.items():
            try:
                if log_file.exists():
                    size = log_file.stat().st_size
                    info["total_size"] += size
                    
                    # Count entries
                    with open(log_file) as f:
                        entry_count = sum(1 for _ in f)
                    
                    info["platforms"][platform] = {
                        "size": size,
                        "entries": entry_count
                    }
            except Exception as e:
                logger.error(f"Error getting info for {platform}: {e}")
                
        return info
    
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
    
    def start(self) -> None:
        """Start the pipeline."""
        if self.running:
            return
            
        self.running = True
        self._flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
        self._flush_thread.start()
    
    def stop(self) -> None:
        """Stop the pipeline."""
        if not self.running:
            return
            
        self.running = False
        if self._flush_thread:
            self._flush_thread.join()
        self.flush()
    
    def _flush_loop(self) -> None:
        """Background thread for periodic flushing."""
        while self.running:
            time.sleep(self.config.batch_timeout)
            self.flush()
    
    def __del__(self):
        """Cleanup on deletion."""
        self.stop() 
