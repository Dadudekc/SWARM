"""
Message History Implementation
----------------------------
Provides persistent message history functionality for the unified message system.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from .unified_message_system import Message, MessageHistory

logger = logging.getLogger('dreamos.messaging.history')

class PersistentMessageHistory(MessageHistory):
    """Persistent message history implementation."""
    
    def __init__(self, history_dir: Path, max_history: int = 10000):
        """Initialize history.
        
        Args:
            history_dir: Directory for history storage
            max_history: Maximum number of messages to keep
        """
        self.history_dir = history_dir
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.max_history = max_history
        
        # In-memory history
        self._history: List[Message] = []
        
        # Load existing history
        self._load_history()
    
    def _load_history(self) -> None:
        """Load existing history from disk."""
        try:
            history_file = self.history_dir / "message_history.json"
            if history_file.exists():
                with open(history_file, 'r') as f:
                    data = json.load(f)
                    self._history = [
                        Message.from_dict(msg_data)
                        for msg_data in data
                    ]
                    
                logger.info(f"Loaded {len(self._history)} historical messages")
        except Exception as e:
            logger.error(f"Error loading message history: {e}")
    
    def _save_history(self) -> None:
        """Save history to disk."""
        try:
            history_file = self.history_dir / "message_history.json"
            with open(history_file, 'w') as f:
                json.dump(
                    [msg.to_dict() for msg in self._history],
                    f,
                    indent=2
                )
                
            logger.info(f"Saved {len(self._history)} historical messages")
        except Exception as e:
            logger.error(f"Error saving message history: {e}")
    
    async def record(self, message: Message) -> bool:
        """Record a message in history.
        
        Args:
            message: Message to record
            
        Returns:
            bool: True if message was successfully recorded
        """
        try:
            # Add to history
            self._history.append(message)
            
            # Trim history if needed
            if len(self._history) > self.max_history:
                self._history = self._history[-self.max_history:]
            
            # Save to disk
            self._save_history()
            
            logger.info(f"Recorded message {message.message_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error recording message: {e}")
            return False
    
    async def get_history(
        self,
        agent_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Message]:
        """Get message history with optional filtering.
        
        Args:
            agent_id: Optional agent ID to filter by
            start_time: Optional start time to filter by
            end_time: Optional end time to filter by
            limit: Optional maximum number of messages to return
            
        Returns:
            List[Message]: List of historical messages
        """
        try:
            # Apply filters
            filtered = self._history
            
            if agent_id:
                filtered = [
                    msg for msg in filtered
                    if msg.sender_id == agent_id or msg.recipient_id == agent_id
                ]
            
            if start_time:
                filtered = [
                    msg for msg in filtered
                    if msg.timestamp >= start_time
                ]
            
            if end_time:
                filtered = [
                    msg for msg in filtered
                    if msg.timestamp <= end_time
                ]
            
            # Apply limit
            if limit:
                filtered = filtered[-limit:]
            
            logger.info(f"Retrieved {len(filtered)} historical messages")
            return filtered
            
        except Exception as e:
            logger.error(f"Error getting message history: {e}")
            return []
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        try:
            self._save_history()
            logger.info("Message history cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}") 