"""
Log Entry Module
---------------
Defines the structure and validation for log entries.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Union, List, Any
from .log_level import LogLevel

@dataclass
class LogEntry:
    """Represents a log entry."""
    
    message: str
    platform: str = "default"
    level: LogLevel = LogLevel.INFO
    timestamp: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate and convert fields."""
        # Validate message
        if not self.message or not isinstance(self.message, str):
            raise ValueError("Message must be a non-empty string")
            
        # Validate platform
        if not self.platform or not isinstance(self.platform, str):
            raise ValueError("Platform must be a non-empty string")
            
        # Convert string level to LogLevel if needed
        if isinstance(self.level, str):
            self.level = LogLevel.from_str(self.level)
        elif not isinstance(self.level, LogLevel):
            raise ValueError(f"Invalid level type: {type(self.level)}")
            
        # Ensure timestamp is a datetime object
        if not isinstance(self.timestamp, datetime):
            self.timestamp = datetime.fromisoformat(self.timestamp)
            
        # Ensure tags is a list
        if not isinstance(self.tags, list):
            self.tags = []
            
        # Ensure metadata is a dict
        if not isinstance(self.metadata, dict):
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            'message': self.message,
            'platform': self.platform,
            'level': self.level.name,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata,
            'tags': self.tags
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogEntry':
        """Create a LogEntry from a dictionary.
        
        Args:
            data: Dictionary with log entry data
            
        Returns:
            LogEntry instance
        """
        # Validate required fields
        if 'message' not in data:
            raise ValueError("Missing required field: message")
        if 'platform' not in data:
            raise ValueError("Missing required field: platform")
            
        # Handle legacy format
        if isinstance(data.get('timestamp'), str):
            timestamp = datetime.fromisoformat(data['timestamp'])
        else:
            timestamp = data.get('timestamp', datetime.now())
            
        return cls(
            message=data['message'],
            platform=data['platform'],
            level=LogLevel.from_str(data.get('level', 'INFO')),
            timestamp=timestamp,
            tags=data.get('tags', []),
            metadata=data.get('metadata', {})
        )

    def _asdict(self) -> Dict[str, Any]:
        """Legacy compatibility method.
        
        Returns:
            Dictionary representation
        """
        return self.to_dict()

    def __eq__(self, other: Any) -> bool:
        """Compare two LogEntry instances."""
        if not isinstance(other, LogEntry):
            return False
        return (
            self.message == other.message and
            self.level == other.level and
            self.timestamp == other.timestamp and
            self.platform == other.platform and
            self.tags == other.tags and
            self.metadata == other.metadata
        )

    def __hash__(self) -> int:
        """Get hash value for the entry."""
        return hash((
            self.message,
            self.level,
            self.timestamp,
            self.platform,
            frozenset(self.tags),
            frozenset(self.metadata.items())
        ))

    def __str__(self) -> str:
        """Get string representation."""
        return f"[{self.level.name}] {self.message}"
        