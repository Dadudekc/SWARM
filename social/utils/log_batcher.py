"""Log batcher module for handling batched log operations."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class LogBatcher:
    """Handles batching of logs for efficient processing."""
    
    def __init__(self, batch_size: int = 100, flush_interval: float = 60.0):
        """Initialize the log batcher.
        
        Args:
            batch_size: Maximum number of logs to batch before flushing
            flush_interval: Time in seconds between automatic flushes
        """
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.batch: List[Dict[str, Any]] = []
        self.last_flush = datetime.now()
        
    def add_log(self, log_entry: Dict[str, Any]) -> None:
        """Add a log entry to the current batch.
        
        Args:
            log_entry: Dictionary containing log data
        """
        self.batch.append(log_entry)
        if len(self.batch) >= self.batch_size:
            self.flush()
            
    def flush(self) -> List[Dict[str, Any]]:
        """Flush the current batch of logs.
        
        Returns:
            List of flushed log entries
        """
        if not self.batch:
            return []
            
        flushed = self.batch.copy()
        self.batch.clear()
        self.last_flush = datetime.now()
        return flushed
        
    def should_flush(self) -> bool:
        """Check if the batch should be flushed based on time.
        
        Returns:
            True if the batch should be flushed
        """
        return (datetime.now() - self.last_flush).total_seconds() >= self.flush_interval 
