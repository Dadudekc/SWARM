"""Common messaging types for Dream.OS."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional


class MessageMode(Enum):
    """Message modes for different types of communication."""
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
    """Represents a message in the Dream.OS system."""
    from_agent: str
    to_agent: str
    content: str
    mode: MessageMode = MessageMode.NORMAL
    priority: MessagePriority = MessagePriority.NORMAL
    message_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    status: str = "queued"
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}
        if self.message_id is None:
            self.message_id = f"{self.timestamp.isoformat()}-{self.from_agent}-{self.to_agent}"

    def format_content(self) -> str:
        """Format message content with mode prefix."""
        return f"{self.mode.value} {self.content}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to a dictionary."""
        return {
            "message_id": self.message_id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "content": self.content,
            "mode": self.mode.value,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        mode_val = data.get("mode", MessageMode.NORMAL.value)
        if mode_val in MessageMode.__members__:
            mode = MessageMode[mode_val]
        else:
            mode = MessageMode(mode_val)

        prio_val = data.get("priority", MessagePriority.NORMAL.value)
        if isinstance(prio_val, str) and prio_val in MessagePriority.__members__:
            priority = MessagePriority[prio_val]
        else:
            priority = MessagePriority(prio_val)

        return cls(
            from_agent=data["from_agent"],
            to_agent=data["to_agent"],
            content=data["content"],
            mode=mode,
            priority=priority,
            message_id=data.get("message_id"),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            status=data.get("status", "queued"),
            metadata=data.get("metadata", {}),
        )

    def validate(self) -> bool:
        try:
            if not self.content:
                raise ValueError("Message content cannot be empty")
            if not self.from_agent or not self.to_agent:
                raise ValueError("Both from_agent and to_agent must be specified")
            if not isinstance(self.priority, MessagePriority):
                raise ValueError("Invalid message priority")
            return True
        except Exception:
            return False
