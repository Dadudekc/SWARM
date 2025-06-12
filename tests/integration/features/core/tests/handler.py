"""Test handler for features integration tests."""

from typing import Dict, Any, Optional

class TestHandler:
    """Test handler implementation."""
    
    def __init__(self):
        self.handled_events: Dict[str, Any] = {}
    
    def handle(self, event: str, data: Any) -> bool:
        """Handle a test event."""
        self.handled_events[event] = data
        return True
    
    def get_handled_event(self, event: str) -> Optional[Any]:
        """Get handled event data."""
        return self.handled_events.get(event) 