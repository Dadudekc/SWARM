from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class Message:
    """Message data class."""
    
    from_agent: str
    to_agent: str
    content: str
    mode: str = "normal"
    priority: int = 0
    timestamp: datetime = None
    status: str = "queued"
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now()
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "content": self.content,
            "mode": self.mode,
            "priority": self.priority,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status,
            "metadata": self.metadata or {}
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create message from dictionary."""
        if "timestamp" in data:
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data) 