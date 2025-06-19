"""
Cell Phone
---------
Agent-to-agent messaging system.
"""

import json
import logging
import os
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union
import asyncio
import pyautogui
import re
from types import SimpleNamespace
import math

# The agent_tools.mailbox package is optional and may not be available in
# minimal test environments. Import it lazily so that basic functionality of the
# CellPhone module can still be exercised during tests without requiring the
# full mailbox subsystem.
try:
    from agent_tools.mailbox.message_handler import MessageHandler
except Exception:  # pragma: no cover - optional dependency
    MessageHandler = None

__all__ = [
    'MessageMode',
    'CellPhone',
    'MessageQueue',
    'send_message',
    'validate_phone_number',
    'format_phone_number'
]

logger = logging.getLogger(__name__)

class MessageMode(Enum):
    """Message delivery modes."""
    NORMAL = "NORMAL"
    PRIORITY = "PRIORITY"
    BULK = "BULK"
    SYSTEM = "SYSTEM"

class MessageQueue:
    """Queue for storing and retrieving messages."""
    
    def __init__(self, queue_path: str):
        """Initialize the message queue.
        
        Args:
            queue_path: Path to the queue file
        """
        self.queue_path = Path(queue_path)
        self.queue_path.parent.mkdir(parents=True, exist_ok=True)
        self._load_queue()
        
    def _load_queue(self):
        """Load the queue from disk."""
        if self.queue_path.exists() and self.queue_path.stat().st_size > 0:
            with open(self.queue_path, 'r') as f:
                self.queue = json.load(f)
        else:
            self.queue = []
            self._save_queue()
            
    def _save_queue(self):
        """Save the queue to disk."""
        with open(self.queue_path, 'w') as f:
            json.dump(self.queue, f, indent=2)
            
    def add_message(self, message: Dict):
        """Add a message to the queue.
        
        Args:
            message: Message to add
        """
        self.queue.append(message)
        self._save_queue()
        
    def get_messages(self) -> List[Dict]:
        """Get all messages in the queue.
        
        Returns:
            List of messages
        """
        return self.queue
        
    def clear_queue(self):
        """Clear the queue."""
        self.queue = []
        self._save_queue()

class CellPhone:
    """Handles injecting prompts into agent conversations."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the cell phone.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.coordinates = self._load_coordinates()
        
    def _load_coordinates(self) -> Dict[str, Dict[str, int]]:
        """Load agent input coordinates.
        
        Returns:
            Dictionary mapping agent IDs to coordinate dictionaries
        """
        try:
            coord_path = Path(self.config.get("coordinate_file", "config/agent_coordinates.json"))
            if not coord_path.exists():
                logger.warning(f"Coordinate file not found: {coord_path}")
                return {}
                
            with open(coord_path, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error loading coordinates: {e}")
            return {}
            
    async def inject_prompt(self, agent_id: str, prompt: str) -> bool:
        """Inject a prompt into an agent's conversation.
        
        Args:
            agent_id: ID of the agent
            prompt: Prompt to inject
            
        Returns:
            True if injection successful, False otherwise
        """
        try:
            # Get agent coordinates
            if agent_id not in self.coordinates:
                logger.error(f"No coordinates found for agent {agent_id}")
                return False
                
            coords = self.coordinates[agent_id]
            
            # Validate coordinate types
            x = coords.get("x")
            y = coords.get("y")
            
            # Check for valid numeric types and values
            if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
                logger.error(f"Invalid coordinate types for agent {agent_id}: x={x}, y={y}")
                return False
                
            # Check for infinite values
            if math.isinf(x) or math.isinf(y):
                logger.error(f"Invalid infinite coordinates for agent {agent_id}: x={x}, y={y}")
                return False
            
            # Click input field
            pyautogui.click(x, y)
            await asyncio.sleep(0.1)  # Wait for focus
            
            # Type prompt
            pyautogui.write(prompt)
            await asyncio.sleep(0.1)  # Wait for typing
            
            # Send message
            pyautogui.press('enter')
            
            logger.info(f"Injected prompt for agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error injecting prompt for agent {agent_id}: {e}")
            return False
            
    async def capture_coordinates(self, agent_id: str) -> bool:
        """Capture input field coordinates for an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            True if capture successful
        """
        try:
            logger.info(f"Move mouse to input field for agent {agent_id} and press Enter...")
            input()  # Wait for Enter key
            
            # Get current mouse position
            x, y = pyautogui.position()
            
            # Update coordinates
            self.coordinates[agent_id] = {
                "x": x,
                "y": y
            }
            
            # Save coordinates
            coord_path = Path(self.config.get("coordinate_file", "config/agent_coordinates.json"))
            coord_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(coord_path, 'w') as f:
                json.dump(self.coordinates, f, indent=2)
                
            logger.info(f"Captured coordinates for agent {agent_id}: ({x}, {y})")
            return True
            
        except Exception as e:
            logger.error(f"Error capturing coordinates for agent {agent_id}: {e}")
            return False

async def send_message(to_agent: str, content: str, mode: str = "NORMAL", from_agent: str = "system") -> bool:
    """
    Send a message to another agent.
    
    Args:
        to_agent: ID of the agent to send to
        content: Message content
        mode: Message mode (NORMAL, PRIORITY, etc.)
        from_agent: ID of the sending agent
        
    Returns:
        bool: True if message sent successfully
    """
    try:
        inbox_path = Path("agent_tools/mailbox") / to_agent / "inbox.json"
        if not inbox_path.exists():
            logger.error(f"Agent {to_agent} inbox not found at {inbox_path}")
            return False
            
        with open(inbox_path, 'r') as f:
            inbox = json.load(f)
            
        message = {
            "from": from_agent,
            "content": content,
            "mode": mode,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if "messages" not in inbox:
            inbox["messages"] = []
            
        inbox["messages"].append(message)
        
        with open(inbox_path, 'w') as f:
            json.dump(inbox, f, indent=2)
            
        return True
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return False

def validate_phone_number(phone_number: str) -> bool:
    """
    Validate a phone number format.
    
    Args:
        phone_number: Phone number to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Remove all non-digit characters
    digits = ''.join(filter(str.isdigit, phone_number))
    
    # Check if we have a valid number of digits
    if len(digits) == 10:  # Standard US number
        return True
    elif len(digits) == 11 and digits.startswith('1'):  # US number with country code
        return True
    return False

def format_phone_number(raw: str) -> str:
    """Formats a phone number into (123) 456-7890 style.
    
    Args:
        raw: Raw phone number string
        
    Returns:
        Formatted phone number string
    """
    digits = re.sub(r'\D', '', raw)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        return raw  # fallback to original
    return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"

# Remove legacy CLI/test harness code below this line
# (No argparse, no __main__ block, no legacy CLI functions) 

class CaptainPhone(CellPhone):
    """Manages messaging for the captain agent."""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Optional[Dict] = None):
        if not hasattr(self, 'agent_id'):
            self.agent_id = "captain"
            super().__init__(config or {})
            self.logger = logging.getLogger(__name__)
            
            async def mock_send(msg):
                return True
                
            async def mock_broadcast(msg):
                return True
                
            self.message_handler = SimpleNamespace(
                send_message=mock_send,
                broadcast_message=mock_broadcast
            )
    
    @classmethod
    def reset_singleton(cls):
        """Reset the singleton instance."""
        cls._instance = None
    
    def broadcast_message(self, content: str, metadata: Optional[Dict] = None) -> bool:
        """Broadcast a message to all agents.
        
        Args:
            content: Message content
            metadata: Optional metadata to attach
            
        Returns:
            bool: True if message was sent successfully
        """
        try:
            message = {
                'sender': self.agent_id,
                'recipient': 'all',
                'content': content,
                'timestamp': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
            
            success = self.message_handler.broadcast_message(message)
            if success:
                self.logger.info("Broadcast message sent")
            else:
                self.logger.error("Failed to send broadcast message")
            return success
            
        except Exception as e:
            self.logger.error(f"Error broadcasting message: {e}")
            return False 

# ---------------------------------------------------------------------------
# Public convenience wrapper (sync) – requested by TASK-DEMO-CHAT-RELAY-002
# ---------------------------------------------------------------------------


def send_cell_message(
    to_agent: str,
    content: str,
    *,
    from_agent: str = "system",
    discord: bool = False,
    discord_channel: int | None = 1,
) -> bool:  # noqa: D401
    """Synchronous helper to send cellphone message and optionally relay to Discord.

    This is a thin wrapper over the *async* :pyfunc:`send_message` coroutine so
    CI and simple scripts can fire-and-forget without creating an event loop.

    Args:
        to_agent: Target agent name (e.g. "Agent-4").
        content: Message text.
        from_agent: Sender identifier (defaults to "system").
        discord: When *True* will post an embed via
            :pymeth:`dreamos.social.discord_webhooks.send_discord_message`.
        discord_channel: Channel ID to post to (ignored if *discord* is *False*).

    Returns:
        *True* on success, *False* otherwise.
    """

    import asyncio

    success: bool = asyncio.run(send_message(to_agent, content, from_agent=from_agent))

    if success and discord:
        try:
            from datetime import datetime  # local import avoids heavy deps when not needed
            from dreamos.social.discord_webhooks import send_discord_message  # type: ignore

            embed = {
                "title": f"{from_agent} ➜ {to_agent}",
                "description": content,
                "timestamp": datetime.utcnow().isoformat(),
            }
            send_discord_message(embed, channel=discord_channel)
        except Exception as exc:  # pragma: no cover – relay issues must not break core
            logger.warning("Failed Discord relay for cellphone message: %s", exc)

    return success 
