"""
Log Entry Module
---------------
Defines the structure and validation for log entries.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Union
from .log_level import LogLevel

@dataclass
class LogEntry:
    """A single log entry with metadata."""
    message: str
    level: Union[str, LogLevel] = LogLevel.INFO
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    platform: str = "general"
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        """Convert string level to LogLevel if needed."""
        if isinstance(self.level, str):
            self.level = LogLevel.from_str(self.level)

    def to_dict(self) -> Dict:
        """Convert entry to dictionary format."""
        return {
            "message": self.message,
            "level": self.level.name if isinstance(self.level, LogLevel) else str(self.level),
            "timestamp": self.timestamp,
            "platform": self.platform,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'LogEntry':
        """Create LogEntry from dictionary."""
        if "message" not in data:
            raise ValueError("LogEntry requires a message field")
        
        # Convert level string to LogLevel if needed
        if "level" in data and isinstance(data["level"], str):
            data["level"] = LogLevel.from_str(data["level"])
            
        return cls(**data)

    def __str__(self) -> str:
        """Get string representation."""
        return f"[{self.level}] {self.message}" 
