"""
Log Writer Module
----------------
Handles writing log entries to files in various formats.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
import json
from enum import Enum
from dataclasses import dataclass
import os
import logging
import tempfile
from contextlib import contextmanager
import platform

logger = logging.getLogger(__name__)

# Import appropriate locking mechanism based on platform
if platform.system() == 'Windows':
    import msvcrt
    import win32file
    import win32con
    import pywintypes
    LOCK_EX = win32con.LOCKFILE_EXCLUSIVE_LOCK
    LOCK_SH = 0  # Shared lock not used
    LOCK_NB = win32con.LOCKFILE_FAIL_IMMEDIATELY
    LOCK_UN = 0  # Unlock not needed, handled by closing file
else:
    import fcntl
    LOCK_EX = fcntl.LOCK_EX
    LOCK_SH = fcntl.LOCK_SH
    LOCK_NB = fcntl.LOCK_NB
    LOCK_UN = fcntl.LOCK_UN

class LogLevel(Enum):
    """Log levels for entries."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

@dataclass
class LogEntry:
    """Represents a single log entry."""
    platform: str
    status: str
    message: str
    level: str = "INFO"
    timestamp: Optional[datetime] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary."""
        return {
            "platform": self.platform,
            "status": self.status,
            "message": self.message,
            "level": self.level,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
            "metadata": self.metadata,
            "error": self.error
        }

class LogWriter:
    """Handles writing log entries to files."""
    
    def __init__(self, log_dir: Union[str, Path]):
        """Initialize the log writer.
        
        Args:
            log_dir: Directory to store log files
        """
        self.log_dir = Path(log_dir)
        self._ensure_log_directory()
    
    def _ensure_log_directory(self) -> None:
        """Ensure log directory exists and is writable."""
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            # Test write permissions
            test_file = self.log_dir / ".test_write"
            try:
                test_file.touch()
                test_file.unlink()
            except Exception as e:
                raise PermissionError(f"Log directory {self.log_dir} is not writable: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to set up log directory: {str(e)}")
            raise
    
    @contextmanager
    def _get_file_lock(self, file_path: Path):
        """Get a file lock for thread-safe operations.
        
        Args:
            file_path: Path to lock
        """
        lock_file = file_path.with_suffix(file_path.suffix + '.lock')
        hfile = None
        try:
            # Create lock file
            lock_file.parent.mkdir(parents=True, exist_ok=True)
            with open(lock_file, 'w') as f:
                if platform.system() == 'Windows':
                    try:
                        # Get file handle
                        hfile = win32file._get_osfhandle(f.fileno())
                        # Create overlapped structure
                        overlapped = pywintypes.OVERLAPPED()
                        # Lock the file (5 args only)
                        win32file.LockFileEx(hfile, LOCK_EX | LOCK_NB, 0, 1, overlapped)
                    except pywintypes.error as e:
                        if e.winerror == 33:  # ERROR_LOCK_VIOLATION
                            raise IOError("File is locked by another process")
                        raise
                else:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                yield
        finally:
            if hfile is not None:
                try:
                    # Create overlapped structure for unlock
                    overlapped = pywintypes.OVERLAPPED()
                    win32file.UnlockFileEx(hfile, 0, 1, overlapped)  # 5 args only
                except:
                    pass
            if lock_file.exists():
                lock_file.unlink()
    
    def write_log(
        self,
        entry: Union[LogEntry, Dict[str, Any]],
        format: str = "json"
    ) -> bool:
        """Write a log entry to file with thread safety.
        
        Args:
            entry: Log entry to write
            format: Output format (json or text)
            
        Returns:
            bool: True if write was successful
        """
        try:
            if isinstance(entry, dict):
                entry = LogEntry(**entry)
            
            # Create platform-specific log file
            log_file = self.log_dir / f"{entry.platform}_operations.{format}"
            
            # Ensure directory exists
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write entry with file locking
            with self._get_file_lock(log_file):
                # Determine file mode based on existence
                mode = 'w' if not log_file.exists() else 'a'
                
                # Write entry to file
                with open(log_file, mode, encoding='utf-8') as f:
                    if format == "json":
                        json.dump(entry.to_dict(), f, default=str)
                        f.write("\n")
                    else:
                        # Text format
                        f.write(f"{entry.timestamp} [{entry.level:8}] {entry.message}\n")
                        if entry.error:
                            f.write(f"Error: {entry.error}\n")
                        if entry.metadata:
                            f.write(f"Metadata: {json.dumps(entry.metadata)}\n")
                        f.write("\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Error writing log: {str(e)}")
            return False
    
    def read_logs(
        self,
        platform: str,
        format: str = "json",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Read logs for a platform with thread safety.
        
        Args:
            platform: Platform to read logs for
            format: Log file format
            start_time: Start time filter
            end_time: End time filter
            
        Returns:
            List of log entries
        """
        try:
            log_file = self.log_dir / f"{platform}_operations.{format}"
            if not log_file.exists():
                return []
            
            entries = []
            with self._get_file_lock(log_file):
                with open(log_file, "r", encoding='utf-8') as f:
                    if format == "json":
                        for line in f:
                            entry = json.loads(line)
                            if self._is_in_time_range(entry, start_time, end_time):
                                entries.append(entry)
                    else:  # text format
                        current_entry = {}
                        for line in f:
                            if line.startswith("["):
                                if current_entry:
                                    entries.append(current_entry)
                                current_entry = self._parse_text_entry(line)
                            elif current_entry:
                                self._update_text_entry(current_entry, line)
                        if current_entry:
                            entries.append(current_entry)
            
            return entries
            
        except Exception as e:
            logger.error(f"Error reading logs: {str(e)}")
            return []
    
    def clear_logs(self, platform: Optional[str] = None) -> bool:
        """Clear logs for a platform or all platforms with thread safety.
        
        Args:
            platform: Platform to clear logs for (None for all)
            
        Returns:
            bool: True if clear was successful
        """
        try:
            if platform:
                log_files = [self.log_dir / f"{platform}_operations.json",
                           self.log_dir / f"{platform}_operations.txt"]
            else:
                log_files = list(self.log_dir.glob("*_operations.*"))
            
            for log_file in log_files:
                if log_file.exists():
                    with self._get_file_lock(log_file):
                        log_file.unlink()
            
            return True
            
        except Exception as e:
            logger.error(f"Error clearing logs: {str(e)}")
            return False
    
    def _is_in_time_range(
        self,
        entry: Dict[str, Any],
        start_time: Optional[datetime],
        end_time: Optional[datetime]
    ) -> bool:
        """Check if entry is within time range.
        
        Args:
            entry: Log entry
            start_time: Start time
            end_time: End time
            
        Returns:
            bool: True if entry is within range
        """
        if not start_time and not end_time:
            return True
        
        try:
            entry_time = datetime.fromisoformat(entry["timestamp"])
            
            if start_time and entry_time < start_time:
                return False
            if end_time and entry_time > end_time:
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error checking time range: {str(e)}")
            return False
    
    def _parse_text_entry(self, line: str) -> Dict[str, Any]:
        """Parse a text format log entry.
        
        Args:
            line: Log line
            
        Returns:
            Dict containing entry data
        """
        try:
            timestamp_str = line[1:line.find("]")]
            level = line[line.find("]")+2:line.find(":")]
            message = line[line.find(":")+2:].strip()
            
            return {
                "timestamp": timestamp_str,
                "level": level,
                "message": message,
                "error": None,
                "metadata": {}
            }
        except Exception as e:
            logger.error(f"Error parsing text entry: {str(e)}")
            return {}
    
    def _update_text_entry(self, entry: Dict[str, Any], line: str) -> None:
        """Update a text format log entry with additional data.
        
        Args:
            entry: Entry to update
            line: Line to parse
        """
        try:
            line = line.strip()
            if line.startswith("Error:"):
                entry["error"] = line[7:]
            elif line.startswith("Metadata:"):
                try:
                    entry["metadata"] = json.loads(line[9:])
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing metadata: {str(e)}")
        except Exception as e:
            logger.error(f"Error updating text entry: {str(e)}")

def write_json_log(platform: str, status: str, message: str, level: str = "INFO", 
                  tags: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None,
                  error: Optional[str] = None) -> None:
    """Helper function to write a log entry.
    
    Args:
        platform: Platform name
        status: Operation status
        message: Log message
        level: Log level
        tags: Optional tags
        metadata: Optional metadata
        error: Optional error message
    """
    try:
        entry = LogEntry(
            platform=platform,
            status=status,
            message=message,
            level=level,
            tags=tags,
            metadata=metadata,
            error=error
        )
        writer = LogWriter(os.getenv("LOG_DIR", "logs"))
        writer.write_log(entry, format="json")
    except Exception as e:
        logger.error(f"Error in write_json_log: {str(e)}") 