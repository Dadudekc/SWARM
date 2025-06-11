"""
Discord Integration Module

Provides Discord webhook integration for bridge monitoring and notifications.
"""

import json
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional

import aiohttp

logger = logging.getLogger(__name__)

class EventType(Enum):
    """Types of events that can be sent to Discord."""
    STARTUP = "startup"
    SHUTDOWN = "shutdown"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SUCCESS = "success"

class DiscordHook:
    """Handles Discord webhook integration for notifications."""
    
    def __init__(self, webhook_url: Optional[str] = None):
        """Initialize the Discord hook.
        
        Args:
            webhook_url: Optional Discord webhook URL
        """
        self.webhook_url = webhook_url
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def start(self):
        """Start the Discord hook."""
        if self.webhook_url:
            self.session = aiohttp.ClientSession()
            
    async def stop(self):
        """Stop the Discord hook."""
        if self.session:
            await self.session.close()
            self.session = None
            
    async def send_event(self, event_type: EventType, message: str, data: Optional[Dict[str, Any]] = None):
        """Send an event to Discord.
        
        Args:
            event_type: Type of event
            message: Event message
            data: Optional event data
        """
        if not self.webhook_url or not self.session:
            return
            
        try:
            # Create embed
            embed = {
                "title": event_type.value.upper(),
                "description": message,
                "color": self._get_color(event_type),
                "timestamp": datetime.now().isoformat()
            }
            
            # Add data if provided
            if data:
                embed["fields"] = [
                    {"name": k, "value": str(v), "inline": True}
                    for k, v in data.items()
                ]
                
            # Create payload
            payload = {
                "embeds": [embed]
            }
            
            # Send webhook
            async with self.session.post(
                self.webhook_url,
                json=payload
            ) as response:
                if response.status != 204:
                    logger.error(f"Failed to send Discord webhook: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error sending Discord webhook: {e}")
            
    def _get_color(self, event_type: EventType) -> int:
        """Get color for event type.
        
        Args:
            event_type: Type of event
            
        Returns:
            int: Color code
        """
        colors = {
            EventType.STARTUP: 0x00ff00,  # Green
            EventType.SHUTDOWN: 0xff0000,  # Red
            EventType.ERROR: 0xff0000,     # Red
            EventType.WARNING: 0xffff00,   # Yellow
            EventType.INFO: 0x0000ff,      # Blue
            EventType.SUCCESS: 0x00ff00    # Green
        }
        return colors.get(event_type, 0x808080)  # Default to gray 