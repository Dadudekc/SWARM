"""
Persistent Queue Module

Provides a persistent queue implementation that can survive process restarts.
"""

import os
import json
import time
import threading
from typing import Any, Dict, List, Optional
from pathlib import Path
from queue import Queue, Empty

class PersistentQueue:
    """A queue that persists its contents to disk."""
    
    def __init__(self, queue_dir: str, max_size: int = 1000):
        """Initialize the persistent queue.
        
        Args:
            queue_dir: Directory to store queue files
            max_size: Maximum number of items in memory queue
        """
        self.queue_dir = Path(queue_dir)
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        
        self.memory_queue = Queue(maxsize=max_size)
        self.lock = threading.Lock()
        
        # Load existing items from disk
        self._load_from_disk()
        
    def _load_from_disk(self) -> None:
        """Load queue items from disk."""
        for file in sorted(self.queue_dir.glob("*.json")):
            try:
                with open(file, 'r') as f:
                    item = json.load(f)
                self.memory_queue.put(item)
            except Exception as e:
                print(f"Error loading queue item from {file}: {e}")
                
    def _save_to_disk(self, item: Dict[str, Any]) -> None:
        """Save a queue item to disk.
        
        Args:
            item: Item to save
        """
        timestamp = int(time.time() * 1000)
        filename = f"{timestamp}.json"
        filepath = self.queue_dir / filename
        
        try:
            with open(filepath, 'w') as f:
                json.dump(item, f)
        except Exception as e:
            print(f"Error saving queue item to {filepath}: {e}")
            
    def put(self, item: Dict[str, Any]) -> None:
        """Put an item in the queue.
        
        Args:
            item: Item to add to queue
        """
        with self.lock:
            self._save_to_disk(item)
            self.memory_queue.put(item)
            
    def get(self, block: bool = True, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Get an item from the queue.
        
        Args:
            block: Whether to block until an item is available
            timeout: Maximum time to wait for an item
            
        Returns:
            Item from queue or None if queue is empty
        """
        try:
            item = self.memory_queue.get(block=block, timeout=timeout)
            return item
        except Empty:
            return None
            
    def qsize(self) -> int:
        """Get the current queue size."""
        return self.memory_queue.qsize()
        
    def empty(self) -> bool:
        """Check if the queue is empty."""
        return self.memory_queue.empty()
        
    def full(self) -> bool:
        """Check if the queue is full."""
        return self.memory_queue.full()
        
    def clear(self) -> None:
        """Clear the queue."""
        with self.lock:
            while not self.memory_queue.empty():
                try:
                    self.memory_queue.get_nowait()
                except Empty:
                    break
                    
            # Remove all queue files
            for file in self.queue_dir.glob("*.json"):
                try:
                    file.unlink()
                except Exception as e:
                    print(f"Error removing queue file {file}: {e}")
                    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all items in the queue.
        
        Returns:
            List of all items in the queue
        """
        items = []
        with self.lock:
            while not self.memory_queue.empty():
                try:
                    items.append(self.memory_queue.get_nowait())
                except Empty:
                    break
                    
            # Put items back in queue
            for item in items:
                self.memory_queue.put(item)
                
        return items 