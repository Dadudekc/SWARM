"""
Log Batcher Module
-----------------
Provides functionality for batching log messages before writing them.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json

class LogBatcher:
    """Batches log messages before writing them."""
    
    def __init__(self, batch_size: int = 100, flush_interval: float = 5.0):
        """Initialize the log batcher.
        
        Args:
            batch_size: Maximum number of messages to batch before flushing
            flush_interval: Maximum time in seconds to wait before flushing
        """
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.batch: List[Dict[str, Any]] = []
        self.last_flush = datetime.now()
    
    def add(self, message: Dict[str, Any]) -> None:
        """Add a message to the current batch.
        
        Args:
            message: Log message to add
        """
        self.batch.append({
            **message,
            'timestamp': datetime.now().isoformat()
        })
        
        if len(self.batch) >= self.batch_size:
            self.flush()
    
    def flush(self) -> Optional[List[Dict[str, Any]]]:
        """Flush the current batch if it's not empty.
        
        Returns:
            List of batched messages if any were flushed, None otherwise
        """
        if not self.batch:
            return None
            
        messages = self.batch.copy()
        self.batch.clear()
        self.last_flush = datetime.now()
        return messages
    
    def should_flush(self) -> bool:
        """Check if the batch should be flushed based on time.
        
        Returns:
            True if the batch should be flushed, False otherwise
        """
        return (datetime.now() - self.last_flush).total_seconds() >= self.flush_interval
    
    def get_batch_size(self) -> int:
        """Get the current number of messages in the batch.
        
        Returns:
            Number of messages in the current batch
        """
        return len(self.batch) 