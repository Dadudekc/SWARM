"""
Base classes for authentication components.
"""

from datetime import datetime
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class ExpirableMixin:
    """Mixin providing expiration-related functionality."""
    created_at: datetime
    expires_at: datetime
    data: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.data is None:
            self.data = {}
    
    @property
    def is_valid(self) -> bool:
        """Check if the object is still valid."""
        return datetime.now() < self.expires_at
    
    @property
    def time_remaining(self) -> float:
        """Get remaining time in seconds."""
        return max(0, (self.expires_at - datetime.now()).total_seconds()) 