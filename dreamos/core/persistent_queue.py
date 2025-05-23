"""
Persistent Queue

A file-based persistent queue implementation with file locking to prevent race conditions.
"""

import json
import os
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger('persistent_queue')

class PersistentQueue:
    """A file-based persistent queue with file locking."""
    
    def __init__(self, queue_file: str = "runtime/queue/messages.json"):
        """Initialize the persistent queue.
        
        Args:
            queue_file: Path to the JSON file used for the queue
        """
        self.queue_file = Path(queue_file)
        self.lock_file = self.queue_file.with_suffix('.lock')
        
        # Create queue directory if it doesn't exist
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize queue file if it doesn't exist
        if not self.queue_file.exists():
            self._write_queue([])
    
    def _acquire_lock(self, timeout: int = 10) -> bool:
        """Acquire a lock file to prevent race conditions.
        
        Args:
            timeout: Maximum time to wait for lock in seconds
            
        Returns:
            bool: True if lock was acquired, False if timeout
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            if not self.lock_file.exists():
                try:
                    with open(self.lock_file, 'w') as f:
                        f.write(str(os.getpid()))
                    return True
                except Exception as e:
                    logger.error(f"Error acquiring lock: {e}")
            time.sleep(0.1)
        return False
    
    def _release_lock(self):
        """Release the lock file."""
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
        except Exception as e:
            logger.error(f"Error releasing lock: {e}")
    
    def _read_queue(self) -> List[Dict]:
        """Read the current queue from file."""
        try:
            with open(self.queue_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading queue: {e}")
            return []
    
    def _write_queue(self, queue: List[Dict]):
        """Write the queue to file."""
        try:
            with open(self.queue_file, 'w') as f:
                json.dump(queue, f, indent=2)
        except Exception as e:
            logger.error(f"Error writing queue: {e}")
    
    def enqueue(self, message: Dict) -> bool:
        """Add a message to the queue.
        
        Args:
            message: Message to add (should be JSON serializable)
            
        Returns:
            bool: True if message was queued successfully
        """
        if not self._acquire_lock():
            logger.error("Failed to acquire lock for enqueue")
            return False
            
        try:
            queue = self._read_queue()
            message['timestamp'] = datetime.now().isoformat()
            message['status'] = 'queued'
            queue.append(message)
            self._write_queue(queue)
            logger.info(f"Message queued: {message.get('to_agent', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"Error enqueueing message: {e}")
            return False
        finally:
            self._release_lock()
    
    def dequeue(self) -> Optional[Dict]:
        """Remove and return the next message from the queue.
        
        Returns:
            Optional[Dict]: Next message or None if queue is empty
        """
        if not self._acquire_lock():
            logger.error("Failed to acquire lock for dequeue")
            return None
            
        try:
            queue = self._read_queue()
            if not queue:
                return None
                
            message = queue.pop(0)
            self._write_queue(queue)
            logger.info(f"Message dequeued: {message.get('to_agent', 'unknown')}")
            return message
        except Exception as e:
            logger.error(f"Error dequeuing message: {e}")
            return None
        finally:
            self._release_lock()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current queue status.
        
        Returns:
            Dict containing queue statistics
        """
        if not self._acquire_lock():
            logger.error("Failed to acquire lock for status check")
            return {"queue_size": 0, "messages": []}
            
        try:
            queue = self._read_queue()
            return {
                "queue_size": len(queue),
                "messages": queue
            }
        except Exception as e:
            logger.error(f"Error getting queue status: {e}")
            return {"queue_size": 0, "messages": []}
        finally:
            self._release_lock()
    
    def clear(self):
        """Clear all messages from the queue."""
        if not self._acquire_lock():
            logger.error("Failed to acquire lock for clear")
            return
            
        try:
            self._write_queue([])
            logger.info("Queue cleared")
        except Exception as e:
            logger.error(f"Error clearing queue: {e}")
        finally:
            self._release_lock()

    def shutdown(self):
        """Clean up resources and release any locks."""
        try:
            self._release_lock()
            logger.info("Queue shutdown complete")
        except Exception as e:
            logger.error(f"Error during queue shutdown: {e}") 