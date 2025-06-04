from __future__ import annotations

"""Shared messaging definitions."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
from uuid import uuid4
import logging


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
    NORMAL = "[NORMAL]"
    PRIORITY = "[PRIORITY]"
    BULK = "[BULK]"
    SELF_TEST = "[SELF_TEST]"
    PROMPT = "[PROMPT]"
    DEVLOG = "[DEVLOG]"
    SYSTEM = "[SYSTEM]"
    COMMAND = "[COMMAND]"


class MessagePriority(Enum):
    """Message priority levels."""
    LOWEST = 0
    LOW = 1
    NORMAL = 2
    HIGH = 3
    HIGHEST = 4
    CRITICAL = 5


@dataclass
class Message:
    """Unified message structure."""

    from_agent: str
    to_agent: str
    content: str
    mode: MessageMode = MessageMode.NORMAL
    priority: MessagePriority = MessagePriority.NORMAL
    message_id: Optional[str] = None
    timestamp: datetime = None
    metadata: Optional[Dict[str, Any]] = None
    status: str = "queued"

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}
        if self.message_id is None:
            self.message_id = str(uuid4())

    def format_content(self) -> str:
        return f"{self.mode.value} {self.content}" if self.content else self.mode.value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "content": self.content,
            "mode": self.mode.value,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        return cls(
            from_agent=data.get("from_agent") or data.get("sender_id"),
            to_agent=data.get("to_agent") or data.get("recipient_id"),
            content=data["content"],
            mode=MessageMode(data["mode"] if not isinstance(data["mode"], int) else MessageMode(data["mode"])),
            priority=MessagePriority(data["priority"] if not isinstance(data["priority"], str) else MessagePriority[data["priority"]]),
            message_id=data.get("message_id"),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata"),
            status=data.get("status", "queued"),
        )

    def validate(self) -> bool:
        try:
            if not self.content:
                raise ValueError("Message content cannot be empty")
            if not isinstance(self.priority, MessagePriority):
                raise ValueError("Invalid priority type")
            if not self.from_agent or not self.to_agent:
                raise ValueError("Both from_agent and to_agent must be specified")
            return True
        except Exception as exc:
            logging.getLogger(__name__).error("Message validation failed: %s", exc)
            return False

__all__ = ["Message", "MessageMode", "MessagePriority"]
