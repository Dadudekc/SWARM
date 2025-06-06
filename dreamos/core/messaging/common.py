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
class MessageContext:
    """Context for message processing."""
    message_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: Optional[str] = None
    destination: Optional[str] = None
    priority: MessagePriority = MessagePriority.NORMAL
    mode: MessageMode = MessageMode.NORMAL
    type: MessageType = MessageType.COMMAND

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "message_id": self.message_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "source": self.source,
            "destination": self.destination,
            "priority": self.priority.name,
            "mode": self.mode.name,
            "type": self.type.name
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MessageContext':
        """Create context from dictionary."""
        return cls(
            message_id=data.get("message_id", str(uuid4())),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
            metadata=data.get("metadata", {}),
            source=data.get("source"),
            destination=data.get("destination"),
            priority=MessagePriority[data.get("priority", "NORMAL")],
            mode=MessageMode[data.get("mode", "NORMAL")],
            type=MessageType[data.get("type", "COMMAND")]
        )

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

    # Backwards compatibility property
    @property
    def sender_id(self) -> str:
        """Alias for ``from_agent`` used in older code."""
        return self.from_agent
    
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

__all__ = ["Message", "MessageContext", "MessageMode", "MessagePriority", "MessageType"]
