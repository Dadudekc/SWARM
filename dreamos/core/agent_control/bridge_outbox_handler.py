"""
Bridge Outbox Handler

Handles outbox operations for bridge communication.
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class BridgeOutboxHandler:
    """Handles outbox operations for bridge communication."""
    
    def __init__(self, outbox_path: str):
        """Initialize the outbox handler.
        
        Args:
            outbox_path: Path to the outbox file
        """
        self.outbox_path = Path(outbox_path)
        self.outbox_path.parent.mkdir(parents=True, exist_ok=True)
        
    def _load_outbox(self) -> List[Dict[str, Any]]:
        """Load messages from outbox.
        
        Returns:
            List of messages in outbox
        """
        try:
            if not self.outbox_path.exists():
                return []
            with self.outbox_path.open('r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading outbox: {e}")
            return []
            
    def _save_outbox(self, messages: List[Dict[str, Any]]) -> None:
        """Save messages to outbox.
        
        Args:
            messages: List of messages to save
        """
        try:
            with self.outbox_path.open('w') as f:
                json.dump(messages, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving outbox: {e}")
            
    async def send_message(
        self,
        to_bridge: str,
        message: Dict[str, Any]
    ) -> bool:
        """Send a message to a bridge.
        
        Args:
            to_bridge: Bridge to send message to
            message: Message to send
            
        Returns:
            True if message was sent successfully
        """
        try:
            messages = self._load_outbox()
            messages.append({
                "to": to_bridge,
                "message": message,
                "timestamp": time.time()
            })
            self._save_outbox(messages)
            return True
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
            
    async def get_messages(
        self,
        bridge: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get messages for a bridge.
        
        Args:
            bridge: Bridge to get messages for
            limit: Optional limit on number of messages
            
        Returns:
            List of messages for bridge
        """
        try:
            messages = self._load_outbox()
            bridge_messages = [
                msg for msg in messages
                if msg["to"] == bridge
            ]
            if limit:
                bridge_messages = bridge_messages[-limit:]
            return bridge_messages
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return []
            
    async def clear_messages(self, bridge: Optional[str] = None) -> bool:
        """Clear messages from outbox.
        
        Args:
            bridge: Optional bridge to clear messages for
            
        Returns:
            True if messages were cleared successfully
        """
        try:
            if bridge:
                messages = self._load_outbox()
                messages = [
                    msg for msg in messages
                    if msg["to"] != bridge
                ]
                self._save_outbox(messages)
            else:
                self._save_outbox([])
            return True
        except Exception as e:
            logger.error(f"Error clearing messages: {e}")
            return False 
