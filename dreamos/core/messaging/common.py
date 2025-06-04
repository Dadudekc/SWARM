from __future__ import annotations

"""
Common messaging structures for Dream.OS.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import uuid4
from .enums import MessageMode, MessagePriority, MessageType
import logging


@dataclass
class Message:
    """Base message structure."""
    content: str
    to_agent: str
    from_agent: str = "system"
    mode: MessageMode = MessageMode.NORMAL
    priority: MessagePriority = MessagePriority.NORMAL
    type: MessageType = MessageType.COMMAND
    timestamp: datetime = field(default_factory=datetime.now)
    message_id: str = field(default_factory=lambda: str(uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)
    response_to: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "content": self.content,
            "to_agent": self.to_agent,
            "from_agent": self.from_agent,
            "mode": self.mode.name,
            "priority": self.priority.name,
            "type": self.type.name,
            "timestamp": self.timestamp.isoformat(),
            "message_id": self.message_id,
            "metadata": self.metadata,
            "response_to": self.response_to
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary."""
        return cls(
            content=data["content"],
            to_agent=data["to_agent"],
            from_agent=data.get("from_agent", "system"),
            mode=MessageMode[data.get("mode", "NORMAL")],
            priority=MessagePriority[data.get("priority", "NORMAL")],
            type=MessageType[data.get("type", "COMMAND")],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            message_id=data["message_id"],
            metadata=data.get("metadata", {}),
            response_to=data.get("response_to")
        )
    
    def validate(self) -> bool:
        """Validate message fields."""
        if not self.content or not self.to_agent:
            return False
        if not isinstance(self.mode, MessageMode):
            return False
        if not isinstance(self.priority, MessagePriority):
            return False
        if not isinstance(self.type, MessageType):
            return False
        return True

__all__ = ["Message", "MessageMode", "MessagePriority", "MessageType"]
