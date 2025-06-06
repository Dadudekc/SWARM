"""
Log Writer Module
----------------
Handles writing log entries to files in various formats.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Union, TextIO
import json
from enum import Enum
from dataclasses import dataclass
import os
import logging
import tempfile
from contextlib import contextmanager
import platform as platform_module  # Rename to avoid conflict
import threading
import portalocker
import stat
import shutil
import time
import atexit
from datetime import timedelta

from .log_entry import LogEntry
from social.utils.log_config import LogConfig
from dreamos.core.config.config_manager import ConfigManager
from dreamos.core.monitoring.metrics import LogMetrics

logger = logging.getLogger(__name__)

# Import appropriate locking mechanism based on platform
if platform_module.system() == 'Windows':
    import msvcrt
    import win32file
    import win32con
    import win32api
    import pywintypes
    LOCK_EX = win32con.LOCKFILE_EXCLUSIVE_LOCK
    LOCK_SH = 0  # Shared lock not used
    LOCK_NB = win32con.LOCKFILE_FAIL_IMMEDIATELY
    LOCK_UN = 0  # Unlock not needed, handled by closing file
    
    # Try to import win32security, but don't fail if not available
    try:
        import win32security
        import ntsecuritycon as con
        HAS_WIN32SECURITY = True
    except ImportError:
        logger.warning("win32security not available, will use basic Windows permissions")
        HAS_WIN32SECURITY = False
else:
    import fcntl
    LOCK_EX = fcntl.LOCK_EX
    LOCK_SH = fcntl.LOCK_SH
    LOCK_NB = fcntl.LOCK_NB
    LOCK_UN = fcntl.LOCK_UN
    HAS_WIN32SECURITY = False

class LogLevel(Enum):
    """Log levels for entries."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogWriter:
    """Handles writing log entries to files."""
    
    def __init__(self, log_dir: str, config: LogConfig):
        """Initialize log writer.
        
        Args:
            log_dir: Directory to store log files
        """
        self.log_dir = Path(log_dir).resolve()
        self.config = config
        self._file_handles = {}
        self._lock = threading.Lock()
        self._file_locks = {}
        self.rotator = None  # Will be set by LogManager
        
        # Register cleanup on exit
        atexit.register(self._cleanup_all_locks)
        
        # Ensure log directory exists with proper permissions
        self._ensure_log_dir()
    
    def _ensure_log_dir(self) -> None:
        """Ensure log directory exists with proper permissions."""
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            if platform_module.system() != 'nt':  # Not Windows
                os.chmod(self.log_dir, 0o700)
        except Exception as e:
            logger.error(f"Failed to create log directory: {e}")
            raise
    
    def _cleanup_all_locks(self) -> None:
        """Clean up all file locks."""
        for file_path, lock_info in list(self._file_locks.items()):
            try:
                if 'file' in lock_info:
                    lock_info['file'].close()
            except Exception as e:
                logger.error(f"Error cleaning up lock for {file_path}: {e}")
            finally:
                self._file_locks.pop(file_path, None)
    
    @contextmanager
    def _get_file_lock(self, file_path: Union[str, Path], mode: str = 'a', timeout: float = 5.0) -> TextIO:
        """Get a file lock for writing.
        
        Args:
            file_path: Path to file
            mode: File open mode ('a' for append, 'w' for write)
            timeout: Maximum time to wait for lock in seconds
            
        Yields:
            File handle with lock
            
        Raises:
            TimeoutError: If lock cannot be acquired within timeout
            IOError: If file cannot be opened
        """
        file_path = Path(file_path).resolve()
        lock_file = file_path.with_suffix(file_path.suffix + '.lock')
        start_time = time.time()
        
        try:
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Try to acquire lock
            while time.time() - start_time < timeout:
                try:
                    if platform_module.system() == 'Windows':
                        # Try to create/access lock file
                        handle = win32file.CreateFile(
                            str(lock_file),
                            win32con.GENERIC_READ | win32con.GENERIC_WRITE,
                            0,  # No sharing
                            None,
                            win32con.OPEN_ALWAYS,
                            win32con.FILE_ATTRIBUTE_NORMAL,
                            None
                        )
                        
                        # Try to lock the file
                        try:
                            win32file.LockFileEx(
                                handle,
                                LOCK_EX | LOCK_NB,
                                0,
                                0xFFFFFFFF,
                                pywintypes.OVERLAPPED()
                            )
                            # Lock acquired
                            break
                        except pywintypes.error as e:
                            # Lock failed, close handle and retry
                            win32file.CloseHandle(handle)
                            if e.winerror != 33:  # ERROR_LOCK_VIOLATION
                                raise
                            time.sleep(0.1)
                            continue
                    else:
                        # Unix-style locking
                        f = open(lock_file, 'a')
                        try:
                            fcntl.flock(f.fileno(), LOCK_EX | LOCK_NB)
                            # Lock acquired
                            break
                        except IOError:
                            f.close()
                            time.sleep(0.1)
                            continue
                except Exception as e:
                    if time.time() - start_time >= timeout:
                        raise TimeoutError(f"Could not acquire lock for {file_path} after {timeout} seconds")
                    time.sleep(0.1)
                    continue
            
            # Open the actual file
            try:
                f = open(file_path, mode)
                if platform_module.system() == 'Windows':
                    self._file_locks[file_path] = {'handle': handle, 'file': f}
                else:
                    self._file_locks[file_path] = {'file': f, 'lock_file': lock_file}
                yield f
            except Exception as e:
                # Clean up lock if file open fails
                if platform_module.system() == 'Windows':
                    win32file.CloseHandle(handle)
                else:
                    fcntl.flock(f.fileno(), LOCK_UN)
                    f.close()
                raise IOError(f"Could not open file {file_path}: {e}")
                
        except Exception as e:
            if isinstance(e, TimeoutError):
                raise
            raise IOError(f"Error acquiring lock for {file_path}: {e}")
            
        finally:
            # Clean up lock
            if file_path in self._file_locks:
                lock_info = self._file_locks[file_path]
                try:
                    if platform_module.system() == 'Windows':
                        win32file.UnlockFileEx(
                            lock_info['handle'],
                            0,
                            0xFFFFFFFF,
                            pywintypes.OVERLAPPED()
                        )
                        win32file.CloseHandle(lock_info['handle'])
                    else:
                        fcntl.flock(lock_info['file'].fileno(), LOCK_UN)
                    lock_info['file'].close()
                except Exception as e:
                    logger.error(f"Error releasing lock for {file_path}: {e}")
                finally:
                    self._file_locks.pop(file_path, None)
    
    def write_log(self, platform_or_entry: Union[str, Dict[str, Any]], level: Optional[str] = None, message: Optional[str] = None, format: str = "json") -> None:
        """Write a log entry.
        
        Args:
            platform_or_entry: Either platform name or complete log entry dict
            level: Log level (if platform_or_entry is platform name)
            message: Log message (if platform_or_entry is platform name)
            format: Output format ("json" or "text")
        """
        try:
            if isinstance(platform_or_entry, dict):
                entry = platform_or_entry
                platform = entry.get('platform', 'unknown')
            else:
                platform = platform_or_entry
                entry = {
                    'platform': platform,
                    'level': level,
                    'message': message,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Handle log level
            level = entry.get('level')
            if level:
                try:
                    level = LogLevel(level.upper())
                except ValueError:
                    raise ValueError(f"Invalid log level: {level}")
            
            # Create log entry
            log_entry = {
                'timestamp': entry.get('timestamp', datetime.now().isoformat()),
                'level': level.value if isinstance(level, LogLevel) else level,
                'message': entry.get('message', ''),
                'platform': platform,
                'status': entry.get('status', 'info'),
                'tags': entry.get('tags', []),
                'metadata': entry.get('metadata', {})
            }
            
            # Write entry
            if format == "json":
                self.write_log_json(platform, log_entry)
            else:
                self.write_log_text(platform, log_entry)
                
        except Exception as e:
            logging.error(f"Error writing log: {e}")
            raise

    def write_log_json(self, platform: str, data: Dict[str, Any]) -> None:
        """Write a log entry in JSON format.
        
        Args:
            platform: Platform identifier
            data: Log entry data
        """
        log_file = self.log_dir / f"{platform}.log"
        
        try:
            with self._get_file_lock(log_file, 'a') as f:
                # Read existing entries
                entries = []
                try:
                    content = f.read()
                    if content:
                        try:
                            # Try to parse as JSON array first
                            entries = json.loads(content)
                            if not isinstance(entries, list):
                                entries = [entries]
                        except json.JSONDecodeError:
                            # If not valid JSON array, try line by line
                            entries = []
                            for line in content.splitlines():
                                if line.strip():
                                    try:
                                        entry = json.loads(line)
                                        entries.append(entry)
                                    except json.JSONDecodeError:
                                        logging.warning(f"Skipping invalid JSON line: {line}")
                except Exception as e:
                    logging.error(f"Error reading existing log entries: {e}")
                
                # Add new entry
                entries.append(data)
                
                # Write back all entries
                f.seek(0)
                f.truncate()
                json.dump(entries, f, indent=2)
                f.write('\n')  # Add newline for readability
                
        except Exception as e:
            logging.error(f"Error writing JSON log: {e}")
            raise

    def read_logs(self, platform: str, start_time: Optional[datetime] = None, 
                 end_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Read log entries.
        
        Args:
            platform: Platform identifier
            start_time: Start time filter
            end_time: End time filter
            
        Returns:
            List of log entries
        """
        log_file = self.log_dir / f"{platform}.log"
        entries = []
        
        try:
            with self._get_file_lock(log_file, 'r') as f:
                try:
                    content = f.read()
                    if content:
                        try:
                            # Try to parse as JSON array first
                            entries = json.loads(content)
                            if not isinstance(entries, list):
                                entries = [entries]
                        except json.JSONDecodeError:
                            # If not valid JSON array, try line by line
                            entries = []
                            for line in content.splitlines():
                                if line.strip():
                                    try:
                                        entry = json.loads(line)
                                        entries.append(entry)
                                    except json.JSONDecodeError:
                                        logging.warning(f"Skipping invalid JSON line: {line}")
                except Exception as e:
                    logging.error(f"Error reading log entries: {e}")
                
                # Apply time filters
                if start_time or end_time:
                    filtered_entries = []
                    for entry in entries:
                        try:
                            entry_time = datetime.fromisoformat(entry['timestamp'])
                            if start_time and entry_time < start_time:
                                continue
                            if end_time and entry_time > end_time:
                                continue
                            filtered_entries.append(entry)
                        except (KeyError, ValueError) as e:
                            logging.warning(f"Skipping entry with invalid timestamp: {e}")
                    entries = filtered_entries
                
                return entries
                
        except Exception as e:
            logging.error(f"Error reading logs: {e}")
            return []

    def cleanup_old_logs(self, max_age_days: int) -> None:
        """Clean up old log files.
        
        Args:
            max_age_days: Maximum age of log files in days
        """
        try:
            cutoff_time = datetime.now() - timedelta(days=max_age_days)
            
            for log_file in self.log_dir.glob('*.log'):
                try:
                    if log_file.stat().st_mtime < cutoff_time.timestamp():
                        with self._get_file_lock(log_file) as f:
                            f.close()  # Ensure file is closed before deletion
                        log_file.unlink()
                except Exception as e:
                    logger.error(f"Error cleaning up old log file {log_file}: {e}")
        except Exception as e:
            logger.error(f"Error in cleanup_old_logs: {e}")
            raise

def write_json_log(platform: str, status: str, message: str, level: str = "INFO", 
                  tags: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None,
                  error: Optional[str] = None) -> None:
    """Write a JSON log entry.
    
    Args:
        platform: Platform name
        status: Status of the operation
        message: Log message
        level: Log level (default: INFO)
        tags: Optional list of tags
        metadata: Optional metadata dictionary
        error: Optional error message
    """
    writer = LogWriter(str(Path.cwd() / "logs"))
    entry = LogEntry(
        platform=platform,
        status=status,
        message=message,
        level=level,
        tags=tags,
        metadata=metadata,
        error=error
    )
    writer.write_log(entry) 