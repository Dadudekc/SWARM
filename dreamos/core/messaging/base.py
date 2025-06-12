"""
Base message system for Dream.OS agent communication.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Union
import uuid

class MessageType(Enum):
    """Types of messages in the system."""
    COMMAND = auto()      # System commands
    REQUEST = auto()      # Agent requests
    RESPONSE = auto()     # Agent responses
    BROADCAST = auto()    # System broadcasts
    STATUS = auto()       # Status updates
    ERROR = auto()        # Error messages
    DEBUG = auto()        # Debug messages

class MessagePriority(Enum):
    """Message priority levels."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

@dataclass
class Message:
    """Base message class."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType = MessageType.REQUEST
    priority: MessagePriority = MessagePriority.NORMAL
    sender: str = ""
    recipient: Optional[str] = None
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    requires_ack: bool = False
    ack_received: bool = False
    retry_count: int = 0
    max_retries: int = 3
    parent_id: Optional[str] = None
    correlation_id: Optional[str] = None

class MessageHandler(ABC):
    """Base class for message handlers."""
    
    @abstractmethod
    async def handle_message(self, message: Message) -> None:
        """Handle an incoming message.
        
        Args:
            message: Message to handle
        """
        pass
    
    @abstractmethod
    async def send_message(self, message: Message) -> bool:
        """Send a message.
        
        Args:
            message: Message to send
            
        Returns:
            bool: True if message was sent successfully
        """
        pass
    
    @abstractmethod
    async def acknowledge_message(self, message_id: str) -> bool:
        """Acknowledge receipt of a message.
        
        Args:
            message_id: ID of message to acknowledge
            
        Returns:
            bool: True if acknowledgment was sent successfully
        """
        pass

class MessageQueue(ABC):
    """Base class for message queues."""
    
    @abstractmethod
    async def enqueue(self, message: Message) -> bool:
        """Add a message to the queue.
        
        Args:
            message: Message to enqueue
            
        Returns:
            bool: True if message was enqueued successfully
        """
        pass
    
    @abstractmethod
    async def dequeue(self) -> Optional[Message]:
        """Get the next message from the queue.
        
        Returns:
            Optional[Message]: Next message or None if queue is empty
        """
        pass
    
    @abstractmethod
    async def peek(self) -> Optional[Message]:
        """Peek at the next message without removing it.
        
        Returns:
            Optional[Message]: Next message or None if queue is empty
        """
        pass
    
    @abstractmethod
    async def remove(self, message_id: str) -> bool:
        """Remove a message from the queue.
        
        Args:
            message_id: ID of message to remove
            
        Returns:
            bool: True if message was removed successfully
        """
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all messages from the queue."""
        pass

class MessageRouter(ABC):
    """Base class for message routers."""
    
    @abstractmethod
    async def route_message(self, message: Message) -> bool:
        """Route a message to its destination.
        
        Args:
            message: Message to route
            
        Returns:
            bool: True if message was routed successfully
        """
        pass
    
    @abstractmethod
    async def register_handler(
        self,
        message_type: MessageType,
        handler: MessageHandler
    ) -> None:
        """Register a handler for a message type.
        
        Args:
            message_type: Type of message to handle
            handler: Handler to register
        """
        pass
    
    @abstractmethod
    async def unregister_handler(
        self,
        message_type: MessageType,
        handler: MessageHandler
    ) -> None:
        """Unregister a handler for a message type.
        
        Args:
            message_type: Type of message to handle
            handler: Handler to unregister
        """
        pass

class MessageValidator(ABC):
    """Base class for message validators."""
    
    @abstractmethod
    def validate_message(self, message: Message) -> bool:
        """Validate a message.
        
        Args:
            message: Message to validate
            
        Returns:
            bool: True if message is valid
        """
        pass
    
    @abstractmethod
    def get_validation_errors(self, message: Message) -> List[str]:
        """Get validation errors for a message.
        
        Args:
            message: Message to validate
            
        Returns:
            List[str]: List of validation errors
        """
        pass 
