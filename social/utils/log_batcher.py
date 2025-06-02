"""
Log Batcher Module
-----------------
Handles batching log entries for efficient writing.
"""

from typing import List, Dict, Any, Optional, Deque
from datetime import datetime, timedelta
import time
import threading
import logging
import queue
from collections import deque
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class BatchConfig:
    """Configuration for log batching."""
    batch_size: int = 100
    batch_timeout: float = 60.0
    max_retries: int = 3
    retry_delay: float = 0.1
    test_mode: bool = False

class LogBatcher:
    """Handles batching log entries for efficient writing."""
    
    def __init__(
        self,
        batch_size: int = 100,
        batch_timeout: float = 60.0,
        max_retries: int = 3,
        retry_delay: float = 0.1,
        test_mode: bool = False
    ):
        """Initialize the log batcher.
        
        Args:
            batch_size: Maximum number of entries per batch
            batch_timeout: Maximum time (seconds) to wait before flushing
            max_retries: Maximum number of retries for failed operations
            retry_delay: Delay between retries in seconds
            test_mode: Whether to run in test mode (disables background thread)
        """
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.test_mode = test_mode
        
        # Use deque for better performance with append/pop operations
        self.entries: Deque[Dict[str, Any]] = deque(maxlen=batch_size)
        self.last_flush = datetime.now()
        self._lock = threading.RLock()
        self._flush_event = threading.Event()
        self._flush_thread = None
        
        # Only start background thread if not in test mode
        if not self.test_mode:
            self._start_flush_thread()
    
    def _start_flush_thread(self) -> None:
        """Start the background flush thread."""
        def flush_worker():
            while not self._flush_event.is_set():
                try:
                    if self._should_flush():
                        self.flush()
                    time.sleep(self.retry_delay)
                except Exception as e:
                    logger.error(f"Error in flush worker: {str(e)}")
        
        self._flush_thread = threading.Thread(target=flush_worker, daemon=True)
        self._flush_thread.start()
    
    def add(self, entry: Dict[str, Any]) -> bool:
        """Add a log entry to the batch with retries.
        
        Args:
            entry: Log entry to add
            
        Returns:
            bool: True if entry was added successfully
        """
        for attempt in range(self.max_retries):
            try:
                with self._lock:
                    # Check if we need to flush based on timeout
                    if self._should_flush():
                        self.flush()
                    
                    # Add entry if we have space
                    if len(self.entries) < self.batch_size:
                        self.entries.append(entry)
                        return True
                    
                    # If we're at capacity, try to flush and add
                    if self._should_flush():
                        self.flush()
                        if len(self.entries) < self.batch_size:
                            self.entries.append(entry)
                            return True
                
                # If we couldn't add the entry, wait and retry
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                
            except Exception as e:
                logger.error(f"Error adding entry (attempt {attempt + 1}): {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    return False
        
        return False
    
    def get_entries(self) -> List[Dict[str, Any]]:
        """Get all entries in the current batch with thread safety.
        
        Returns:
            List of log entries
        """
        with self._lock:
            try:
                entries = list(self.entries)
                self.entries.clear()
                self.last_flush = datetime.now()
                return entries
            except Exception as e:
                logger.error(f"Error getting entries: {str(e)}")
                return []
    
    def clear(self) -> None:
        """Clear all entries in the current batch with thread safety."""
        with self._lock:
            try:
                self.entries.clear()
                self.last_flush = datetime.now()
            except Exception as e:
                logger.error(f"Error clearing entries: {str(e)}")
    
    def is_empty(self) -> bool:
        """Check if the batch is empty with thread safety.
        
        Returns:
            bool: True if batch is empty
        """
        with self._lock:
            return len(self.entries) == 0
    
    def _should_flush(self) -> bool:
        """Check if the batch should be flushed.
        
        Returns:
            bool: True if batch should be flushed
        """
        try:
            current_time = datetime.now()
            time_since_last_flush = (current_time - self.last_flush).total_seconds()
            
            return (
                len(self.entries) >= self.batch_size or
                time_since_last_flush >= self.batch_timeout
            )
        except Exception as e:
            logger.error(f"Error checking if should flush: {str(e)}")
            return True  # Flush on error to be safe
    
    def flush(self) -> List[Dict[str, Any]]:
        """Flush the current batch with thread safety.
        
        Returns:
            List of flushed entries
        """
        with self._lock:
            try:
                entries = list(self.entries)
                self.clear()
                return entries
            except Exception as e:
                logger.error(f"Error flushing batch: {str(e)}")
                return []
    
    def shutdown(self) -> None:
        """Shutdown the batcher gracefully."""
        try:
            self._flush_event.set()
            if self._flush_thread and self._flush_thread.is_alive():
                self._flush_thread.join(timeout=5.0)
            self.flush()  # Final flush
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}") 