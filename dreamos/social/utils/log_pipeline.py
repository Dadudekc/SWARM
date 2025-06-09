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
    """Pipeline for handling log entries with batching and platform-specific routing."""
    
    def __init__(self, config: LogConfig):
        """Initialize the log pipeline.
        
        Args:
            config: LogConfig instance containing pipeline configuration
        """
        self.config = config
        self.batch: List[LogEntry] = []
        self.last_batch_time = time.time()
        self.running = False
        
        # Ensure log directory exists
        self.config.log_dir.mkdir(parents=True, exist_ok=True)
    
    def add_entry(self, entry: Dict[str, Any] | LogEntry) -> None:
        """Add a log entry to the pipeline.
        
        Args:
            entry: Dictionary or LogEntry containing log data
        """
        if not self.running:
            return
            
        # Validate required fields
        if isinstance(entry, dict):
            if "platform" not in entry or "message" not in entry:
                raise ValueError("Log entry must contain 'platform' and 'message' fields")
            
            # Set defaults for optional fields
            if "level" not in entry:
                entry["level"] = self.config.level
            if "timestamp" not in entry:
                entry["timestamp"] = datetime.now().isoformat()
                
            entry = LogEntry(**entry)
        
        self.batch.append(entry)
        
        # Check if we need to flush
        if (len(self.batch) >= self.config.batch_size or 
            time.time() - self.last_batch_time >= self.config.batch_timeout):
            self.flush()
    
    def flush(self) -> None:
        """Flush the current batch to log files."""
        if not self.batch:
            return
            
        # Group entries by platform
        platform_entries: Dict[str, List[LogEntry]] = {}
        for entry in self.batch:
            platform = entry.platform
            if platform not in platform_entries:
                platform_entries[platform] = []
            platform_entries[platform].append(entry)
        
        # Write entries to respective log files
        for platform, entries in platform_entries.items():
            log_file = self.config.platforms.get(platform)
            if not log_file:
                log_file = self.config.log_dir / f"{platform}.log"
                self.config.platforms[platform] = log_file
            
            # Ensure log file exists
            log_file.parent.mkdir(parents=True, exist_ok=True)
            log_file.touch(exist_ok=True)
            
            # Write entries
            with log_file.open("a", encoding="utf-8") as f:
                for entry in entries:
                    f.write(json.dumps(entry.to_dict()) + "\n")
        
        # Clear batch and update time
        self.batch.clear()
        self.last_batch_time = time.time()
    
    def get_log_info(self) -> Dict[str, Any]:
        """Get information about log files.
        
        Returns:
            Dictionary containing log file information
        """
        info = {
            "total_size": 0,
            "platforms": {},
            "total_entries": 0
        }
        
        try:
            for platform, log_file in self.config.platforms.items():
                if log_file.exists():
                    size = log_file.stat().st_size
                    info["total_size"] += size
                    
                    # Count entries
                    entry_count = 0
                    with log_file.open("r", encoding="utf-8") as f:
                        for _ in f:
                            entry_count += 1
                    
                    info["platforms"][platform] = {
                        "size": size,
                        "entries": entry_count
                    }
                    info["total_entries"] += entry_count
        except Exception as e:
            print(f"Error getting log info: {e}")
        
        return info
    
    def read_logs(self, platform: str, level: Optional[str] = None) -> List[Dict[str, Any]]:
        """Read log entries for a specific platform.
        
        Args:
            platform: Platform to read logs from
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
    
    def start(self) -> None:
        """Start the pipeline."""
        self.running = True
    
    def stop(self) -> None:
        """Stop the pipeline and flush any remaining entries."""
        self.running = False
        self.flush()
    
    def __del__(self):
        """Cleanup on deletion."""
        self.stop() 
