"""
Log Reader Module
----------------
Handles reading log entries from files.
"""

import os
import json
import logging
import platform
import threading
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import win32file
import win32con
import pywintypes
import portalocker

logger = logging.getLogger(__name__)

class LogReader:
    """Handles reading log entries from files."""
    
    def __init__(self, log_dir: str):
        """Initialize reader."""
        self.log_dir = Path(log_dir)
        self._lock = threading.RLock()
        self._file_locks = {}
        
    def _is_file_locked(self, filepath: str) -> bool:
        """Check if a file is locked on Windows, using robust sharing flags."""
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
            
            # Use all sharing flags for maximum compatibility
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
            
    def _wait_for_file_unlock(self, file_path: str, max_retries: int = 10) -> bool:
        """Wait for file to be unlocked, with more retries and backoff."""
        for attempt in range(max_retries):
            try:
                if platform.system() == 'Windows':
                    if not self._is_file_locked(file_path):
                        return True
                    # Try to force close any open handles
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
        logger.error(f"File {file_path} could not be unlocked after {max_retries} attempts.")
        return False
        
    def read_logs(self, platform: Optional[str] = None, level: Optional[str] = None,
                 limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Read log entries with improved error diagnostics and handle closing."""
        entries = []
        try:
            if platform:
                log_files = [self.log_dir / f"{platform}.log"]
            else:
                log_files = list(self.log_dir.glob("*.log"))
            for log_file in log_files:
                if not log_file.exists():
                    continue
                if not self._wait_for_file_unlock(log_file):
                    logger.warning(f"Could not unlock file {log_file}")
                    continue
                f = None
                try:
                    # Try to change permissions first
                    if platform.system() == 'Windows':
                        os.chmod(str(log_file), 0o666)
                    f = open(log_file, 'r')
                    portalocker.lock(f, portalocker.LOCK_SH)
                    for line in f:
                        try:
                            entry = json.loads(line)
                            logger.debug(f"Read log entry: {entry}")
                            if level:
                                logger.debug(f"Comparing entry level '{entry.get('level')}' to filter '{level}'")
                            if level and entry.get("level") != level:
                                continue
                            entries.append(entry)
                            if limit and len(entries) >= limit:
                                break
                        except json.JSONDecodeError as jde:
                            logger.warning(f"JSON decode error in {log_file}: {jde}")
                            continue
                except Exception as e:
                    logger.error(f"Error reading log file {log_file}: {e}")
                    continue
                finally:
                    if f:
                        try:
                            f.close()
                        except Exception as close_e:
                            logger.warning(f"Error closing file {log_file}: {close_e}")
            entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            if limit:
                entries = entries[:limit]
            return entries
        except Exception as e:
            logger.error(f"Error reading logs: {e}")
            return []
            
    def get_log_info(self) -> Dict[str, Any]:
        """Get information about log files."""
        info = {
            "total_files": 0,
            "total_entries": 0,
            "platforms": {},
            "levels": {},
            "oldest_entry": None,
            "newest_entry": None
        }
        
        try:
            for log_file in self.log_dir.glob("*.log"):
                if not log_file.exists():
                    continue
                if not self._wait_for_file_unlock(log_file):
                    continue
                f = None
                try:
                    # Try to change permissions first
                    if platform.system() == 'Windows':
                        os.chmod(str(log_file), 0o666)
                    f = open(log_file, 'r')
                    portalocker.lock(f, portalocker.LOCK_SH)
                    entry_count = 0
                    for line in f:
                        try:
                            entry = json.loads(line)
                            entry_count += 1
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
                        except json.JSONDecodeError:
                            continue
                    info["total_entries"] += entry_count
                    info["total_files"] += 1
                except Exception as e:
                    logger.error(f"Error reading log file {log_file}: {e}")
                    continue
                finally:
                    if f:
                        try:
                            f.close()
                        except Exception as close_e:
                            logger.warning(f"Error closing file {log_file}: {close_e}")
            return info
        except Exception as e:
            logger.error(f"Error getting log info: {e}")
            return info 