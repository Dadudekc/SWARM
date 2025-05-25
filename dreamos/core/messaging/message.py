"""
Message Module

Defines core message types and structures for the Dream.OS messaging system.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

logger = logging.getLogger('messaging.message')

class MessageMode(Enum):
    """Message delivery modes."""
    RESUME = "[RESUME]"
    SYNC = "[SYNC]"
    VERIFY = "[VERIFY]"
    REPAIR = "[REPAIR]"
    BACKUP = "[BACKUP]"
    RESTORE = "[RESTORE]"
    CLEANUP = "[CLEANUP]"
    CAPTAIN = "[CAPTAIN]"
    TASK = "[TASK]"
    INTEGRATE = "[INTEGRATE]"
    NORMAL = ""  # No additional tags
    PRIORITY = "priority"
    BULK = "bulk"
    SELF_TEST = "[SELF_TEST]"  # For self-test protocol messages

@dataclass
class Message:
    """Represents a message in the Dream.OS system."""
    from_agent: str
    to_agent: str
    content: str
    mode: MessageMode = MessageMode.NORMAL
    priority: int = 0
    timestamp: datetime = None
    status: str = "queued"
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}
            
    def format_content(self) -> str:
        """Format message content with mode prefix."""
        if self.mode == MessageMode.NORMAL:
            return self.content
        return f"{self.mode.value} {self.content}"
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format."""
        return {
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "content": self.format_content(),
            "mode": self.mode.name,
            "priority": self.priority,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status,
            "metadata": self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary format."""
        return cls(
            from_agent=data["from_agent"],
            to_agent=data["to_agent"],
            content=data["content"],
            mode=MessageMode[data["mode"]],
            priority=data["priority"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            status=data["status"],
            metadata=data.get("metadata", {})
        )
        
    def validate(self) -> bool:
        """Validate message fields."""
        try:
            if not self.content:
                raise ValueError("Message content cannot be empty")
            if not 0 <= self.priority <= 5:
                raise ValueError("Priority must be between 0 and 5")
            if not self.from_agent or not self.to_agent:
                raise ValueError("Both from_agent and to_agent must be specified")
            return True
        except Exception as e:
            logger.error(f"Message validation failed: {e}")
            return False 