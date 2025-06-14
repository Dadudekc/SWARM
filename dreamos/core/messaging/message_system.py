"""
Unified Message System
---------------------
Provides a single source of truth for all message handling in Dream.OS.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

from .common import Message, MessageMode
from ..shared.persistent_queue import PersistentQueue as SharedPersistentQueue

logger = logging.getLogger('dreamos.messaging')

# Compatibility alias – older code expected a `MessageRecord` dataclass that was
# later renamed to `Message`.  Expose an alias so legacy imports keep working.
MessageRecord = Message  # type: ignore

class MessageQueue(ABC):
    """Abstract base class for message queue implementations."""
    
    @abstractmethod
    def enqueue(self, message: Message) -> bool:
        """Add message to queue."""
        pass
    
    @abstractmethod
    def get_messages(self) -> List[Message]:
        """Get all pending messages."""
        pass
    
    @abstractmethod
    def acknowledge(self, message_id: str) -> bool:
        """Mark message as processed."""
        pass

class PersistentQueue(MessageQueue):
    """Persistent message queue using JSON storage."""
    
    def __init__(self, queue_dir: Optional[Path] = None):
        """Initialize persistent queue.
        
        Args:
            queue_dir: Directory for queue storage. Defaults to runtime/queues.
        """
        self.queue_dir = queue_dir or Path("runtime/queues")
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        self.pending_file = self.queue_dir / "pending_messages.json"
        self._load_queue()
    
    def _load_queue(self):
        """Load queue from disk."""
        if self.pending_file.exists():
            with open(self.pending_file, 'r') as f:
                self.queue = json.load(f)
        else:
            self.queue = []
    
    def _save_queue(self):
        """Save queue to disk."""
        with open(self.pending_file, 'w') as f:
            json.dump(self.queue, f, indent=2)
    
    def enqueue(self, message: Message) -> bool:
        """Add message to queue."""
        try:
            self.queue.append(message.to_dict())
            self._save_queue()
            return True
        except Exception as e:
            logger.error(f"Failed to enqueue message: {e}")
            return False
    
    def get_messages(self) -> List[Message]:
        """Get all pending messages."""
        try:
            return [Message.from_dict(msg) for msg in self.queue]
        except Exception as e:
            logger.error(f"Failed to get messages: {e}")
            return []
    
    def acknowledge(self, message_id: str) -> bool:
        """Mark message as processed."""
        try:
            self.queue = [
                msg for msg in self.queue
                if msg['message_id'] != message_id
            ]
            self._save_queue()
            return True
        except Exception as e:
            logger.error(f"Failed to acknowledge message {message_id}: {e}")
            return False

class MessageHistory(ABC):
    """Abstract base class for message history implementations."""
    
    @abstractmethod
    def record(self, message: Message) -> bool:
        """Record a message in history."""
        pass
    
    @abstractmethod
    def get_history(self, type: Optional[MessageMode] = None) -> List[Message]:
        """Get message history, optionally filtered by type."""
        pass

class JsonMessageHistory(MessageHistory):
    """Message history implementation using JSON storage."""
    
    def __init__(self, history_file: Optional[Path] = None):
        """Initialize message history.
        
        Args:
            history_file: Path to history file. Defaults to runtime/message_history.json.
        """
        self.history_file = history_file or Path("runtime/message_history.json")
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_history()
    
    def _load_history(self):
        """Load history from disk."""
        if self.history_file.exists():
            with open(self.history_file, 'r') as f:
                self.history = json.load(f)
        else:
            self.history = []
    
    def _save_history(self):
        """Save history to disk."""
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def record(self, message: Message) -> bool:
        """Record a message in history."""
        try:
            self.history.append(message.to_dict())
            self._save_history()
            return True
        except Exception as e:
            logger.error(f"Failed to record message: {e}")
            return False
    
    def get_history(self, type: Optional[MessageMode] = None) -> List[Message]:
        """Get message history, optionally filtered by type."""
        try:
            if type:
                messages = [
                    msg for msg in self.history
                    if msg['type'] == type.name
                ]
            else:
                messages = self.history
            return [Message.from_dict(msg) for msg in messages]
        except Exception as e:
            logger.error(f"Failed to get history: {e}")
            return []

class MessageRouter(ABC):
    """Abstract base class for message routing implementations."""
    
    @abstractmethod
    def route(self, message: Message) -> bool:
        """Route a message to its destination."""
        pass

class MessageSystem:
    """Unified message system for Dream.OS."""
    
    def __init__(
        self,
        queue: Optional[MessageQueue] = None,
        history: Optional[MessageHistory] = None,
        router: Optional[MessageRouter] = None
    ):
        """Initialize message system.
        
        Args:
            queue: Message queue implementation
            history: Message history implementation
            router: Message router implementation
        """
        self.queue = queue or PersistentQueue()
        self.history = history or JsonMessageHistory()
        self.router = router
    
    def send(self, message: Message) -> bool:
        """Send a message.
        
        Args:
            message: Message to send
            
        Returns:
            bool: True if message was sent successfully
        """
        try:
            # Record in history
            self.history.record(message)
            
            # Add to queue
            success = self.queue.enqueue(message)
            if not success:
                logger.error("Failed to enqueue message")
                return False
            
            # Route if router available
            if self.router:
                success = self.router.route(message)
                if not success:
                    logger.error("Failed to route message")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    def receive(self) -> List[Message]:
        """Receive pending messages.
        
        Returns:
            List of pending messages
        """
        try:
            return self.queue.get_messages()
        except Exception as e:
            logger.error(f"Failed to receive messages: {e}")
            return []
    
    def acknowledge(self, message_id: str) -> bool:
        """Acknowledge a message as processed.
        
        Args:
            message_id: ID of message to acknowledge
            
        Returns:
            bool: True if message was acknowledged successfully
        """
        try:
            return self.queue.acknowledge(message_id)
        except Exception as e:
            logger.error(f"Failed to acknowledge message: {e}")
            return False
    
    def get_history(self, type: Optional[MessageMode] = None) -> List[Message]:
        """Get message history.
        
        Args:
            type: Optional message type to filter by
            
        Returns:
            List of historical messages
        """
        try:
            return self.history.get_history(type)
        except Exception as e:
            logger.error(f"Failed to get history: {e}")
            return [] 
