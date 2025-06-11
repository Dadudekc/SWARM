"""
Bridge health model.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class BridgeHealth:
    """Health status information."""
    is_healthy: bool
    last_check: datetime
    error_count: int
    last_error: Optional[str]
    session_active: bool
    message_count: int 