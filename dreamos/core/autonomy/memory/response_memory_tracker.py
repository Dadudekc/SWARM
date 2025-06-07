"""
Response Memory Tracker
---------------------
Tracks processed messages and prevents duplicate processing in the response loop system.
"""

import json
import os
import logging
from typing import Set, Dict, Any
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResponseMemoryTracker:
    """Tracks processed messages to prevent duplicate processing."""
    
    def __init__(self, memory_path: str):
        """Initialize the memory tracker.
        
        Args:
            memory_path: Path to store memory data
        """
        self.memory_path = Path(memory_path)
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        self.processed_hashes: Set[str] = set()
        self._load_memory()
        logger.info(f"Initialized ResponseMemoryTracker at {self.memory_path}")
    
    def _load_memory(self):
        """Load existing memory data."""
        if self.memory_path.exists():
            try:
                with open(self.memory_path, 'r') as f:
                    data = json.load(f)
                    self.processed_hashes = set(data.get("hashes", []))
                logger.info(f"Loaded {len(self.processed_hashes)} processed message hashes")
            except Exception as e:
                logger.error(f"Error loading memory data: {e}")
                self.processed_hashes = set()
    
    def is_processed(self, message_hash: str) -> bool:
        """Check if a message has been processed.
        
        Args:
            message_hash: Hash of the message to check
            
        Returns:
            True if message has been processed
        """
        is_duplicate = message_hash in self.processed_hashes
        if is_duplicate:
            logger.info(f"Skipping duplicate message with hash: {message_hash[:8]}...")
        return is_duplicate
    
    def track_processing(self, message_hash: str, metadata: Dict[str, Any] = None):
        """Track a processed message.
        
        Args:
            message_hash: Hash of the processed message
            metadata: Optional metadata about the processing
        """
        if message_hash not in self.processed_hashes:
            self.processed_hashes.add(message_hash)
            self._save_memory(metadata)
            logger.info(f"Tracked new message with hash: {message_hash[:8]}...")
    
    def _save_memory(self, metadata: Dict[str, Any] = None):
        """Save memory data to file.
        
        Args:
            metadata: Optional metadata to include
        """
        try:
            data = {
                "hashes": list(self.processed_hashes),
                "last_updated": datetime.now().isoformat(),
                "count": len(self.processed_hashes)
            }
            if metadata:
                data["metadata"] = metadata
                
            with open(self.memory_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving memory data: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory tracking statistics.
        
        Returns:
            Dictionary of statistics
        """
        return {
            "processed_count": len(self.processed_hashes),
            "memory_path": str(self.memory_path),
            "last_updated": datetime.now().isoformat()
        } 