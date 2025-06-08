"""
Discord Integration
-----------------
Handles Discord notifications for bridge events.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/discord_hook.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EventType(Enum):
    """Types of bridge events."""
    LOOP_START = "loop_start"
    LOOP_END = "loop_end"
    PROMPT_SUBMITTED = "prompt_submitted"
    PROMPT_FAILED = "prompt_failed"
    RESPONSE_RECEIVED = "response_received"
    ERROR_OCCURRED = "error_occurred"
    HEALTH_CHECK = "health_check"

class DiscordHook:
    """Handles Discord notifications for bridge events."""
    
    def __init__(self, outbox_path: str = "runtime/discord_outbox"):
        """Initialize the Discord hook."""
        self.outbox_path = Path(outbox_path)
        self.outbox_path.mkdir(parents=True, exist_ok=True)
        
    def _format_message(self, 
                       event_type: EventType,
                       agent_id: Optional[str] = None,
                       summary: Optional[str] = None,
                       details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Format a Discord message."""
        message = {
            "type": event_type.value,
            "timestamp": datetime.now().isoformat(),
            "content": {
                "title": self._get_title(event_type),
                "description": summary or "",
                "color": self._get_color(event_type),
                "fields": []
            }
        }
        
        if agent_id:
            message["content"]["fields"].append({
                "name": "Agent",
                "value": agent_id,
                "inline": True
            })
            
        if details:
            for key, value in details.items():
                message["content"]["fields"].append({
                    "name": key.replace("_", " ").title(),
                    "value": str(value),
                    "inline": True
                })
                
        return message
        
    def _get_title(self, event_type: EventType) -> str:
        """Get the title for an event type."""
        titles = {
            EventType.LOOP_START: "🟢 Bridge Loop Started",
            EventType.LOOP_END: "🔴 Bridge Loop Ended",
            EventType.PROMPT_SUBMITTED: "📤 Prompt Submitted",
            EventType.PROMPT_FAILED: "❌ Prompt Failed",
            EventType.RESPONSE_RECEIVED: "📥 Response Received",
            EventType.ERROR_OCCURRED: "⚠️ Error Occurred",
            EventType.HEALTH_CHECK: "💓 Health Check"
        }
        return titles.get(event_type, "Bridge Event")
        
    def _get_color(self, event_type: EventType) -> int:
        """Get the color for an event type."""
        colors = {
            EventType.LOOP_START: 0x00ff00,  # Green
            EventType.LOOP_END: 0xff0000,    # Red
            EventType.PROMPT_SUBMITTED: 0x0000ff,  # Blue
            EventType.PROMPT_FAILED: 0xff0000,     # Red
            EventType.RESPONSE_RECEIVED: 0x00ff00,  # Green
            EventType.ERROR_OCCURRED: 0xffa500,    # Orange
            EventType.HEALTH_CHECK: 0x00ff00       # Green
        }
        return colors.get(event_type, 0x808080)  # Default gray
        
    def send_event(self,
                  event_type: EventType,
                  agent_id: Optional[str] = None,
                  summary: Optional[str] = None,
                  details: Optional[Dict[str, Any]] = None):
        """Send a Discord event notification."""
        try:
            message = self._format_message(event_type, agent_id, summary, details)
            
            # Write to outbox
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bridge_event_{timestamp}.json"
            event_file = self.outbox_path / filename
            
            with open(event_file, 'w') as f:
                json.dump(message, f, indent=2)
                
            logger.info(f"Sent Discord event: {event_type.value}")
            
        except Exception as e:
            logger.error(f"Error sending Discord event: {e}")
            
    def send_health_update(self, metrics: Dict[str, Any]):
        """Send a health check update."""
        status = metrics.get("status", "unknown")
        success_rate = metrics.get("metrics", {}).get("success_rate", 0)
        avg_time = metrics.get("metrics", {}).get("average_processing_time", 0)
        
        summary = f"Bridge Status: {status.upper()}\n"
        summary += f"Success Rate: {success_rate:.1f}%\n"
        summary += f"Avg Processing Time: {avg_time:.1f}s"
        
        self.send_event(
            EventType.HEALTH_CHECK,
            summary=summary,
            details=metrics.get("metrics", {})
        )
        
    def send_prompt_status(self,
                          agent_id: str,
                          prompt_type: str,
                          success: bool,
                          error: Optional[str] = None):
        """Send a prompt status update."""
        event_type = EventType.PROMPT_SUBMITTED if success else EventType.PROMPT_FAILED
        summary = f"{'Successfully' if success else 'Failed to'} process {prompt_type} prompt"
        
        details = {
            "prompt_type": prompt_type,
            "status": "success" if success else "failed"
        }
        
        if error:
            details["error"] = error
            
        self.send_event(event_type, agent_id, summary, details) 
