"""
Agent Status Module

This module provides status tracking and management for agents.
"""

from enum import Enum, auto
from typing import Optional, Dict, Any
from datetime import datetime

class AgentStatus(Enum):
    """Enum representing possible agent states."""
    
    INITIALIZING = auto()
    IDLE = auto()
    BUSY = auto()
    ERROR = auto()
    SHUTDOWN = auto()
    
class AgentStatusInfo:
    """Class for tracking detailed agent status information."""
    
    def __init__(self, 
                 status: AgentStatus = AgentStatus.INITIALIZING,
                 last_updated: Optional[datetime] = None,
                 error_message: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """Initialize agent status info.
        
        Args:
            status: Current agent status
            last_updated: Timestamp of last status update
            error_message: Optional error message if status is ERROR
            metadata: Optional additional status metadata
        """
        self.status = status
        self.last_updated = last_updated or datetime.utcnow()
        self.error_message = error_message
        self.metadata = metadata or {}
        
    def update(self,
              status: Optional[AgentStatus] = None,
              error_message: Optional[str] = None,
              metadata: Optional[Dict[str, Any]] = None) -> None:
        """Update agent status information.
        
        Args:
            status: New status to set
            error_message: New error message to set
            metadata: New metadata to set
        """
        if status is not None:
            self.status = status
        if error_message is not None:
            self.error_message = error_message
        if metadata is not None:
            self.metadata.update(metadata)
        self.last_updated = datetime.utcnow()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert status info to dictionary.
        
        Returns:
            Dictionary representation of status info
        """
        return {
            'status': self.status.name,
            'last_updated': self.last_updated.isoformat(),
            'error_message': self.error_message,
            'metadata': self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentStatusInfo':
        """Create AgentStatusInfo from dictionary.
        
        Args:
            data: Dictionary containing status info
            
        Returns:
            New AgentStatusInfo instance
        """
        return cls(
            status=AgentStatus[data['status']],
            last_updated=datetime.fromisoformat(data['last_updated']),
            error_message=data.get('error_message'),
            metadata=data.get('metadata', {})
        ) 