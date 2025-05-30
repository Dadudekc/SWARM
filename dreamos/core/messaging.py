"""
Shared message types and enums.

This module contains shared types used across the messaging system.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

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
    NORMAL = ""  # No additional tags

@dataclass
class Message:
    """Represents a message with metadata."""
    from_agent: str
    to_agent: str
    content: str
    priority: int
    timestamp: datetime
    status: str = "queued" 