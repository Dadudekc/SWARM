"""
Log Entry Module
---------------
Defines the LogEntry class for representing log entries.
"""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import json
from .log_level import LogLevel

class LogEntry:
    """Represents a single log entry."""
    
    def __init__(
        self,
        message: str,
        level: Union[str, LogLevel] = "INFO",
        platform: Optional[str] = None,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        """Initialize a log entry.
        
        Args:
            message: Log message
            level: Log level (default: INFO)
            platform: Optional platform name
            status: Optional status of the operation
            tags: Optional list of tags
            metadata: Optional metadata dictionary
            error: Optional error message
            timestamp: Optional timestamp (defaults to current time)
        """
        self.message = message
        self.level = level if isinstance(level, LogLevel) else LogLevel[level.upper()]
        self.platform = platform
        self.status = status or "INFO"  # Default status
        self.tags = tags or []
        self.metadata = metadata or {}
        self.error = error
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary.
        
        Returns:
            Dictionary representation of the entry
        """
        return {
            "platform": self.platform,
            "status": self.status,
            "message": self.message,
            "level": self.level.name,
            "tags": self.tags,
            "metadata": self.metadata,
            "error": self.error,
            "timestamp": self.timestamp.isoformat()
        }
    
    def to_json(self) -> str:
        """Convert entry to JSON string.
        
        Returns:
            JSON string representation of the entry
        """
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogEntry':
        """Create entry from dictionary.
        
        Args:
            data: Dictionary containing entry data
            
        Returns:
            LogEntry instance
        """
        # Convert timestamp string to datetime if present
        timestamp = None
        if "timestamp" in data:
            try:
                timestamp = datetime.fromisoformat(data["timestamp"])
            except (ValueError, TypeError):
                pass
                
        return cls(
            message=data["message"],
            level=data.get("level", "INFO"),
            platform=data.get("platform"),
            status=data.get("status"),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            error=data.get("error"),
            timestamp=timestamp
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'LogEntry':
        """Create entry from JSON string.
        
        Args:
            json_str: JSON string containing entry data
            
        Returns:
            LogEntry instance
        """
        return cls.from_dict(json.loads(json_str))
    
    def __str__(self) -> str:
        """Get string representation of entry.
        
        Returns:
            String representation
        """
        return f"[{self.timestamp.isoformat()}] {self.level.name} - {self.platform} - {self.status}: {self.message}"
    
    def __repr__(self) -> str:
        """Get detailed string representation of entry.
        
        Returns:
            Detailed string representation
        """
        return (
            f"LogEntry(message='{self.message}', "
            f"level={self.level.name}, "
            f"platform='{self.platform}', "
            f"status='{self.status}', "
            f"tags={self.tags}, "
            f"metadata={self.metadata}, "
            f"error={self.error}, "
            f"timestamp='{self.timestamp.isoformat()}')"
        )

    def __getitem__(self, key: str) -> Any:
        """Get item by key.
        
        Args:
            key: Key to get
            
        Returns:
            Value for key
            
        Raises:
            KeyError: If key not found
        """
        if key == "platform":
            return self.platform
        elif key == "message":
            return self.message
        elif key == "level":
            return self.level
        elif key == "status":
            return self.status
        elif key == "tags":
            return self.tags
        elif key == "metadata":
            return self.metadata
        elif key == "error":
            return self.error
        elif key == "timestamp":
            return self.timestamp
        else:
            raise KeyError(f"Key not found: {key}") 