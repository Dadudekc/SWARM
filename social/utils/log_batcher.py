"""
Log Batcher Module
----------------
Batches log entries for efficient writing.
"""

import time
from typing import List, Any, Optional

class LogBatcher:
    """Batches log entries for efficient writing."""
    
    def __init__(
        self,
        max_size: int = 100,
        timeout: float = 60.0
    ):
        """Initialize batcher.
        
        Args:
            max_size: Maximum number of entries per batch
            timeout: Maximum time in seconds before batch is flushed
        """
        self.max_size = max_size
        self.timeout = timeout
        self.entries: List[Any] = []
        self.last_flush = time.time()
    
    def add(self, entry: Any) -> bool:
        """Add an entry to the batch.
        
        Args:
            entry: Log entry to add
            
        Returns:
            True if entry was added, False if batch is full
        """
        if len(self.entries) >= self.max_size:
            return False
            
        self.entries.append(entry)
        return True
    
    def get_entries(self) -> List[Any]:
        """Get current batch entries.
        
        Returns:
            List of current entries
        """
        return self.entries
    
    def is_empty(self) -> bool:
        """Check if batch is empty.
        
        Returns:
            True if batch is empty
        """
        return len(self.entries) == 0
    
    def should_flush(self) -> bool:
        """Check if batch should be flushed.
        
        Returns:
            True if batch should be flushed
        """
        if len(self.entries) >= self.max_size:
            return True
            
        if time.time() - self.last_flush >= self.timeout:
            return True
            
        return False
    
    def flush(self) -> List[Any]:
        """Flush the batch.
        
        Returns:
            List of flushed entries
        """
        entries = self.entries.copy()
        self.entries.clear()
        self.last_flush = time.time()
        return entries 