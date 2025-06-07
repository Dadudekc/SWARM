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

from .common import MessageMode
from ..shared.persistent_queue import PersistentQueue as SharedPersistentQueue

logger = logging.getLogger('dreamos.messaging')

@dataclass
class MessageRecord:
    """Standardized message record format."""
    sender_id: str
    recipient_id: str
    content: str
    timestamp: datetime
    message_id: Optional[str] = None
    mode: MessageMode = MessageMode.NORMAL
    priority: int = 0
    status: str = "queued"
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}
        if self.message_id is None:
            self.message_id = f"{self.timestamp.isoformat()}-{self.sender_id}-{self.recipient_id}"
    
    def format_content(self) -> str:
        """Format message content with mode prefix."""
        return f"{self.mode.value} {self.content}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['mode'] = self.mode.name
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MessageRecord':
        """Create from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['mode'] = MessageMode[data['mode']]
        return cls(**data)

class MessageQueue(ABC):
    """Abstract base class for message queue implementations."""
    
    @abstractmethod
    def enqueue(self, message: MessageRecord) -> bool:
        """Add message to queue."""
        pass
    
    @abstractmethod
    def get_messages(self, agent_id: str) -> List[MessageRecord]:
        """Get all pending messages for an agent."""
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
            self.queue = {}
    
    def _save_queue(self):
        """Save queue to disk."""
        with open(self.pending_file, 'w') as f:
            json.dump(self.queue, f, indent=2)
    
    def enqueue(self, message: MessageRecord) -> bool:
        """Add message to queue."""
        try:
            agent_id = message.recipient_id
            if agent_id not in self.queue:
                self.queue[agent_id] = []
            
            self.queue[agent_id].append(message.to_dict())
            self._save_queue()
            return True
        except Exception as e:
            logger.error(f"Failed to enqueue message: {e}")
            return False
    
    def get_messages(self, agent_id: str) -> List[MessageRecord]:
        """Get all pending messages for an agent."""
        try:
            messages = self.queue.get(agent_id, [])
            return [MessageRecord.from_dict(msg) for msg in messages]
        except Exception as e:
            logger.error(f"Failed to get messages for {agent_id}: {e}")
            return []
    
    def acknowledge(self, message_id: str) -> bool:
        """Mark message as processed."""
        try:
            for agent_id in self.queue:
                self.queue[agent_id] = [
                    msg for msg in self.queue[agent_id]
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
    def record(self, message: MessageRecord) -> bool:
        """Record a message in history."""
        pass
    
    @abstractmethod
    def get_history(self, agent_id: Optional[str] = None) -> List[MessageRecord]:
        """Get message history, optionally filtered by agent."""
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
    
    def record(self, message: MessageRecord) -> bool:
        """Record a message in history."""
        try:
            self.history.append(message.to_dict())
            self._save_history()
            return True
        except Exception as e:
            logger.error(f"Failed to record message: {e}")
            return False
    
    def get_history(self, agent_id: Optional[str] = None) -> List[MessageRecord]:
        """Get message history, optionally filtered by agent."""
        try:
            if agent_id:
                messages = [
                    msg for msg in self.history
                    if msg['recipient_id'] == agent_id or msg['sender_id'] == agent_id
                ]
            else:
                messages = self.history
            return [MessageRecord.from_dict(msg) for msg in messages]
        except Exception as e:
            logger.error(f"Failed to get history for {agent_id}: {e}")
            return []


class MessageRouter(ABC):
    """Abstract base class for message routing implementations."""
    
    @abstractmethod
    def route(self, message: MessageRecord) -> bool:
        """Route a message to its destination."""
        pass

class AgentMessageRouter(MessageRouter):
    """Message router implementation for agent communication."""
    
    def __init__(self, message_system: 'MessageSystem'):
        """Initialize router.
        
        Args:
            message_system: Reference to parent MessageSystem for callbacks.
        """
        self.message_system = message_system
    
    def route(self, message: MessageRecord) -> bool:
        """Route a message to its destination."""
        try:
            # For now, just log the routing
            logger.info(
                f"Routing message {message.message_id} from {message.sender_id} "
                f"to {message.recipient_id}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to route message: {e}")
            return False

class MessageSystem:
    """Unified message handling system."""
    
    def __init__(
        self,
        queue: Optional[MessageQueue] = None,
        history: Optional[MessageHistory] = None,
        router: Optional[MessageRouter] = None
    ):
        """Initialize message system.
        
        Args:
            queue: Message queue implementation. Defaults to SharedPersistentQueue.
            history: Message history implementation. Defaults to JsonMessageHistory.
            router: Message router implementation. Defaults to AgentMessageRouter.
        """
        self.queue = queue or SharedPersistentQueue()
        self.history = history or JsonMessageHistory()
        self.router = router or AgentMessageRouter(self)
    
    def send(self, message: MessageRecord) -> bool:
        """Send a message through the system.
        
        Args:
            message: Message to send.
            
        Returns:
            bool: True if message was successfully processed.
        """
        try:
            # Route the message
            if not self.router.route(message):
                return False
            
            # Add to queue
            if not self.queue.enqueue(message):
                return False
            
            # Record in history
            if not self.history.record(message):
                return False
            
            logger.info(f"Message {message.message_id} sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    def receive(self, agent_id: str) -> List[MessageRecord]:
        """Get pending messages for an agent.
        
        Args:
            agent_id: ID of agent to get messages for.
            
        Returns:
            List[MessageRecord]: List of pending messages.
        """
        try:
            messages = self.queue.get_messages(agent_id)
            logger.info(f"Retrieved {len(messages)} messages for {agent_id}")
            return messages
        except Exception as e:
            logger.error(f"Failed to receive messages for {agent_id}: {e}")
            return []
    
    def acknowledge(self, message_id: str) -> bool:
        """Mark a message as processed.
        
        Args:
            message_id: ID of message to acknowledge.
            
        Returns:
            bool: True if message was successfully acknowledged.
        """
        try:
            return self.queue.acknowledge(message_id)
        except Exception as e:
            logger.error(f"Failed to acknowledge message {message_id}: {e}")
            return False
    
    def get_history(self, agent_id: Optional[str] = None) -> List[MessageRecord]:
        """Get message history.
        
        Args:
            agent_id: Optional agent ID to filter history.
            
        Returns:
            List[MessageRecord]: List of historical messages.
        """
        try:
            return self.history.get_history(agent_id)
        except Exception as e:
            logger.error(f"Failed to get history for {agent_id}: {e}")
            return [] 
