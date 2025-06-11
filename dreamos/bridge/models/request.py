"""
Bridge request model.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class BridgeRequest:
    """A request to be processed by the bridge."""
    id: str
    message: str
    timestamp: datetime
    status: str
    response: Optional[str] = None
    error: Optional[str] = None 