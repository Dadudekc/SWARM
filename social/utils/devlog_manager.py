"""
Stub implementation of DevlogManager for testing purposes.
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class DevlogManager:
    """Stub implementation of DevlogManager."""
    
    def __init__(self, *args, **kwargs):
        """Initialize stub DevlogManager."""
        self.logger = logger
    
    def log_event(self, event: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log an event with optional data."""
        if data:
            self.logger.info(f"[Devlog] {event}: {data}")
        else:
            self.logger.info(f"[Devlog] {event}")
    
    def get_log(self, *args, **kwargs) -> str:
        """Get the log contents."""
        return "Stub devlog content"
    
    def clear_log(self, *args, **kwargs) -> bool:
        """Clear the log."""
        return True
    
    def add_entry(self, *args, **kwargs) -> bool:
        """Add an entry to the log."""
        return True 