"""
Log Entry Module
---------------
Defines the structure and validation for log entries.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional

@dataclass
class LogEntry:
    """Represents a single log entry with validation."""
    
    platform: str
    message: str
    level: str = "INFO"
    timestamp: str = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Validate and set defaults after initialization."""
        if not self.platform:
            raise ValueError("Platform must be specified")
        if not self.message:
            raise ValueError("Message must be specified")
            
        # Validate level
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.level not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of: {valid_levels}")
            
        # Set timestamp if not provided
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
            
        # Initialize empty metadata if not provided
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary format.
        
        Returns:
            Dict[str, Any]: Dictionary representation of entry
        """
        return {
            "platform": self.platform,
            "message": self.message,
            "level": self.level,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogEntry':
        """Create LogEntry from dictionary.
        
        Args:
            data: Dictionary containing entry data
            
        Returns:
            LogEntry: New log entry instance
            
        Raises:
            ValueError: If required fields are missing
        """
        required_fields = {"platform", "message"}
        missing_fields = required_fields - set(data.keys())
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
            
        return cls(
            platform=data["platform"],
            message=data["message"],
            level=data.get("level", "INFO"),
            timestamp=data.get("timestamp"),
            metadata=data.get("metadata")
        ) 
