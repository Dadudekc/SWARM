"""
Message Record Module
-------------------
Defines the structure for agent-to-agent messages.
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class MessageRecord:
    """Represents a message between agents."""
    
    from_agent: str
    to_agent: str
    payload: str
    tags: List[str]
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> dict:
        """Convert message to dictionary format."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "payload": self.payload,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MessageRecord':
        """Create message from dictionary format."""
        return cls(
            from_agent=data["from_agent"],
            to_agent=data["to_agent"],
            payload=data["payload"],
            tags=data["tags"],
            timestamp=datetime.fromisoformat(data["timestamp"])
        ) 