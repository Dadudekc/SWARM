"""
Log Writer
---------
Handles writing logs with proper file locking and error handling.
"""

import os
import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from contextlib import contextmanager

from dreamos.core.utils.file_utils import safe_write, safe_read

logger = logging.getLogger(__name__)

class LogWriter:
    """Thread-safe log writer with proper file locking."""
    
    def __init__(self, log_dir: str = "logs"):
        """Initialize the log writer.
        
        Args:
            log_dir: Directory to store logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._file_handles = {}
        
    def _get_log_path(self, platform: str) -> Path:
        """Get path for platform-specific log file.
        
        Args:
            platform: Platform identifier
            
        Returns:
            Path to log file
        """
        return self.log_dir / f"{platform}.log"
    
    def _get_handle_key(self, platform: str, mode: str = 'a') -> str:
        """Get unique key for file handle.
        
        Args:
            platform: Platform identifier
            mode: File open mode
            
        Returns:
            Handle key
        """
        return f"{platform}_{mode}"
    
    @contextmanager
    def _get_file_handle(self, platform: str, mode: str = 'a'):
        """Get file handle with proper locking.
        
        Args:
            platform: Platform identifier
            mode: File open mode
        """
        handle_key = self._get_handle_key(platform, mode)
        
        with self._lock:
            if handle_key not in self._file_handles:
                log_path = self._get_log_path(platform)
                try:
                    self._file_handles[handle_key] = open(log_path, mode, encoding='utf-8')
                except Exception as e:
                    logger.error(f"Failed to open log file {log_path}: {e}")
                    raise
                    
            try:
                yield self._file_handles[handle_key]
            except Exception as e:
                logger.error(f"Error writing to log file: {e}")
                raise
                
    def write_log(self, platform: str, level: str, message: str, **kwargs) -> bool:
        """Write a log entry.
        
        Args:
            platform: Platform identifier
            level: Log level
            message: Log message
            **kwargs: Additional log data
            
        Returns:
            True if successful
        """
        try:
            entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": level,
                "message": message,
                **kwargs
            }
            
            # Write as JSON
            content = json.dumps(entry) + "\n"
            
            with self._get_file_handle(platform) as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())  # Force write to disk
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to write log entry: {e}")
            return False
            
    def read_logs(self, platform: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Read log entries.
        
        Args:
            platform: Platform identifier
            limit: Maximum number of entries to read
            
        Returns:
            List of log entries
        """
        try:
            log_path = self._get_log_path(platform)
            if not log_path.exists():
                return []
                
            content = safe_read(log_path)
            if not content:
                return []
                
            # Parse entries
            entries = []
            for line in content.strip().split('\n'):
                try:
                    entry = json.loads(line)
                    entries.append(entry)
                except json.JSONDecodeError:
                    continue
                    
            # Apply limit
            if limit is not None:
                entries = entries[-limit:]
                
            return entries
            
        except Exception as e:
            logger.error(f"Failed to read logs: {e}")
            return []
            
    def clear_log(self, platform: str) -> bool:
        """Clear log file.
        
        Args:
            platform: Platform identifier
            
        Returns:
            True if successful
        """
        try:
            log_path = self._get_log_path(platform)
            
            with self._lock:
                # Close any open handles
                handle_key = self._get_handle_key(platform)
                if handle_key in self._file_handles:
                    self._file_handles[handle_key].close()
                    del self._file_handles[handle_key]
                    
                # Clear file
                return safe_write(log_path, "")
                
        except Exception as e:
            logger.error(f"Failed to clear log: {e}")
            return False
            
    def close(self):
        """Close all file handles."""
        with self._lock:
            for handle in self._file_handles.values():
                try:
                    handle.close()
                except Exception as e:
                    logger.error(f"Error closing file handle: {e}")
            self._file_handles.clear() 