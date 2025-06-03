"""
Discord Log Manager Module
------------------
Provides functionality for sending logs to Discord via webhooks.
"""

from typing import Dict, Any, Optional
import requests
import logging

class DiscordLogManager:
    # Discord embed colors
    COLORS = {
        'debug': 0x808080,  # Gray
        'info': 0x00ff00,   # Green
        'warning': 0xffff00, # Yellow
        'error': 0xff0000,  # Red
        'critical': 0x800000 # Dark Red
    }
    
    def __init__(self, webhook_url: Optional[str] = None):
        """Initialize the DiscordLogManager.
        
        Args:
            webhook_url: Optional Discord webhook URL
        """
        self.webhook_url = webhook_url
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def _get_color_for_level(self, level: str) -> int:
        """Get Discord embed color for log level.
        
        Args:
            level: Log level (debug, info, warning, error, critical)
            
        Returns:
            Color integer for Discord embed
        """
        return self.COLORS.get(level.lower(), self.COLORS['info'])

    def format_log_for_discord(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Format log payload for Discord embed.
        
        Args:
            payload: Log payload dictionary
            
        Returns:
            Formatted embed dictionary
            
        Raises:
            ValueError: If payload is missing required fields
        """
        required_fields = ['level', 'message', 'timestamp', 'context']
        missing_fields = [field for field in required_fields if field not in payload]
        if missing_fields:
            raise ValueError(f"Missing required fields in log payload: {', '.join(missing_fields)}")
            
        # Create embed
        embed = {
            "title": f"Log: {payload['level'].upper()}",
            "description": payload['message'],
            "color": self._get_color_for_level(payload['level']),
            "timestamp": payload['timestamp'],
            "fields": []
        }
        
        # Add context field
        if 'context' in payload:
            embed['fields'].append({
                "name": "Context",
                "value": payload['context'],
                "inline": True
            })
            
        # Add additional fields
        for key, value in payload.items():
            if key not in ['level', 'message', 'timestamp', 'context']:
                embed['fields'].append({
                    "name": key.capitalize(),
                    "value": str(value),
                    "inline": True
                })
                
        return embed
        
    def send_embed(self, embed: Dict[str, Any]) -> bool:
        """Send an embed to Discord.
        
        Args:
            embed: The embed data to send
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            ValueError: If embed is empty or missing required fields
        """
        if not embed:
            raise ValueError("Empty embed data")
            
        # Validate required fields
        required_fields = ['title', 'description', 'color', 'timestamp']
        missing_fields = [field for field in required_fields if field not in embed]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            
        if not self.webhook_url:
            self.logger.error("No webhook URL configured")
            return False
            
        try:
            response = requests.post(
                self.webhook_url,
                json={"embeds": [embed]},
                timeout=10
            )
            response.raise_for_status()
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending embed: {str(e)}")
            return False 