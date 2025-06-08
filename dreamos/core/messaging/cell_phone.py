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
        if self.queue_path.exists():
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
    """Cell phone for agent communications."""
    
    _instance = None
    
    def __new__(cls, config: Dict):
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Dict):
        """Initialize cell phone.
        
        Args:
            config: Configuration dictionary containing:
                - message_handler: MessageHandler instance
                - agent_id: Agent ID
        """
        if not hasattr(self, 'initialized'):
            self.message_handler = config.get('message_handler')
            if not self.message_handler:
                raise ValueError("message_handler is required in config")
                
            self.agent_id = config.get('agent_id')
            if not self.agent_id:
                raise ValueError("agent_id is required in config")
                
            logger.info(f"Cell phone initialized for agent {self.agent_id}")
            self.initialized = True
    
    @classmethod
    def reset_singleton(cls):
        """Reset singleton instance."""
        cls._instance = None
    
    def send_message(self, to_agent: str, content: str, metadata: Optional[Dict] = None, mode: Optional[str] = None, priority: Optional[str] = None) -> bool:
        """Send message to agent.
        
        Args:
            to_agent: Target agent ID
            content: Message content
            metadata: Optional message metadata
            mode: Optional message mode
            priority: Optional message priority
        Returns:
            bool: True if message sent successfully
        """
        if not content or not to_agent:
            return False
        try:
            return self.message_handler.send_message(
                to_agent=to_agent,
                content=content,
                from_agent=self.agent_id,
                metadata=metadata or {},
                mode=mode,
                priority=priority
            )
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def get_messages(self) -> List[Dict]:
        """Get messages for this agent.
        
        Returns:
            List[Dict]: List of messages
        """
        try:
            return self.message_handler.get_messages(self.agent_id)
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return []
    
    def acknowledge_message(self, message_id: str) -> bool:
        """Acknowledge message receipt.
        
        Args:
            message_id: ID of message to acknowledge
            
        Returns:
            bool: True if message acknowledged successfully
        """
        try:
            return self.message_handler.acknowledge_message(message_id)
        except Exception as e:
            logger.error(f"Error acknowledging message: {e}")
            return False

    def clear_messages(self) -> bool:
        """Clear all messages for this agent."""
        try:
            return self.message_handler.clear_messages(self.agent_id)
        except Exception as e:
            logger.error(f"Error clearing messages: {e}")
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
    # Basic validation - can be enhanced based on requirements
    return bool(phone_number and phone_number.replace('+', '').replace('-', '').replace(' ', '').isdigit())

def format_phone_number(phone_number: str) -> str:
    """
    Format a phone number to a standard format.
    
    Args:
        phone_number: Phone number to format
        
    Returns:
        Formatted phone number
    """
    # Remove all non-digit characters
    digits = ''.join(filter(str.isdigit, phone_number))
    
    # Add country code if missing
    if not digits.startswith('1') and len(digits) == 10:
        digits = '1' + digits
    
    return f"+{digits}"

# Remove legacy CLI/test harness code below this line
# (No argparse, no __main__ block, no legacy CLI functions) 

class CaptainPhone(CellPhone):
    """Manages messaging for the captain agent."""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Dict):
        """Initialize the captain phone.
        
        Args:
            config: Configuration dictionary containing:
                - message_handler: MessageHandler instance
                - agent_id: ID of this agent (should be 'captain')
        """
        if not hasattr(self, 'initialized'):
            super().__init__(config)
            if self.agent_id != 'captain':
                raise ValueError("CaptainPhone must be initialized with agent_id='captain'")
            self.initialized = True
    
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
