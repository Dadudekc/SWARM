"""Async file watcher utility."""

import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)

class AsyncFileWatcher:
    """Asynchronously watches a directory for file changes.
    
    This class provides functionality to monitor a directory for file changes
    using polling. It maintains a cache of file modification times to detect
    changes between polls.
    """
    
    def __init__(self, watch_dir: str, poll_interval: float = 1.0):
        """Initialize file watcher.
        
        Args:
            watch_dir: Directory to watch for changes
            poll_interval: Time between polls in seconds
        """
        self.watch_dir = Path(watch_dir)
        self.poll_interval = poll_interval
        self._file_cache: Dict[str, float] = {}
        self._last_check: Optional[datetime] = None
    
    async def check_for_changes(self) -> List[str]:
        """Check for file changes since last check.
        
        Returns:
            List of paths to changed files
        """
        if not self.watch_dir.exists():
            logger.warning(f"Watch directory {self.watch_dir} does not exist")
            return []
        
        changed_files: List[str] = []
        current_time = datetime.now()
        
        try:
            # Get all files in directory
            files = list(self.watch_dir.glob("**/*"))
            
            # Check each file
            for file_path in files:
                if not file_path.is_file():
                    continue
                
                # Get modification time
                mtime = file_path.stat().st_mtime
                file_str = str(file_path)
                
                # Check if file is new or modified
                if file_str not in self._file_cache or mtime > self._file_cache[file_str]:
                    changed_files.append(file_str)
                    self._file_cache[file_str] = mtime
            
            # Check for deleted files
            deleted_files = set(self._file_cache.keys()) - {str(f) for f in files}
            for file_str in deleted_files:
                del self._file_cache[file_str]
            
            self._last_check = current_time
            
        except Exception as e:
            logger.error(f"Error checking for file changes: {e}")
        
        return changed_files
    
    def get_file_info(self, file_path: str) -> Optional[Dict]:
        """Get information about a watched file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information or None if file not found
        """
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            return None
        
        try:
            stat = path.stat()
            return {
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime),
                "created": datetime.fromtimestamp(stat.st_ctime)
            }
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return None
    
    def clear_cache(self) -> None:
        """Clear the file modification cache."""
        self._file_cache.clear()
        self._last_check = None
    
    @property
    def last_check(self) -> Optional[datetime]:
        """Get timestamp of last check."""
        return self._last_check
    
    @property
    def watched_files(self) -> Set[str]:
        """Get set of currently watched files."""
        return set(self._file_cache.keys()) 
