"""
Shared message types and enums.

This module contains shared types used across the messaging system.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from .enums import MessageMode

@dataclass
class Message:
    """Represents a message with metadata."""
    from_agent: str
    to_agent: str
    content: str
    priority: int
    timestamp: datetime
    status: str = "queued" 
