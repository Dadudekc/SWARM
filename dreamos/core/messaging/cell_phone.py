"""
Cell Phone Messaging Module
-------------------------
Handles SMS and MMS messaging functionality.
"""

import logging
from typing import List, Optional, Dict, Any
import os
from pathlib import Path
from datetime import datetime
from enum import Enum
import argparse

logger = logging.getLogger(__name__)

class MessageMode(Enum):
    NORMAL = "NORMAL"
    PRIORITY = "PRIORITY"
    BULK = "BULK"
    SYSTEM = "SYSTEM"

class CellPhone:
    """Handles agent-to-agent messaging with priority queues and status tracking."""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """Ensure singleton instance of CellPhone."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize messaging system with optional configuration."""
        if not hasattr(self, 'initialized'):
            self.config = config or {}
            self.logger = logging.getLogger(__name__)
            self.queue = MessageQueue()
            self.initialized = True
    
    def _is_valid_agent(self, agent_id: str) -> bool:
        """Validate that the agent ID is properly formatted (starts with 'Agent-')."""
        return isinstance(agent_id, str) and agent_id.startswith("Agent-")
    
    @classmethod
    def reset_singleton(cls):
        """Reset the singleton instance for testing purposes."""
        cls._instance = None
    
    def send_message(
        self,
        to_agent: str,
        content: str,
        mode: str = "NORMAL",
        priority: int = 0,
        from_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Queue a message for delivery to an agent with specified mode and priority."""
        if not content or not to_agent:
            return False

        if not self._is_valid_agent(to_agent):
            return False

        if mode not in [m.value for m in MessageMode]:
            return False

        if not 0 <= priority <= 5:
            return False
            
        message = {
            'to_agent': to_agent,
            'content': content,
            'mode': mode,
            'priority': priority,
            'from_agent': from_agent,
            'metadata': metadata or {},
            'timestamp': datetime.now().isoformat()
        }
        
        return self.queue.add_message(message)
    
    def get_message_status(self, agent_id: str) -> Dict[str, Any]:
        """Get current message status and history for an agent."""
        return self.queue.get_agent_status(agent_id)
    
    def get_message_history(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get complete message history for an agent."""
        return self.queue.get_agent_history(agent_id)
    
    def clear_messages(self, agent_id: str) -> None:
        """Clear all messages and reset status for an agent."""
        self.queue.clear_agent_messages(agent_id)
    
    def shutdown(self) -> None:
        """Shutdown messaging system and clear all queues."""
        self.queue.clear_queue()

class MessageQueue:
    """Manages message queues and status tracking for all agents."""
    
    def __init__(self):
        """Initialize empty message queue and status tracking."""
        self.messages = []
        self.agent_status = {}
    
    def _get_default_status(self) -> Dict[str, Any]:
        """Get empty status structure for new or reset agents."""
        return {
            'message_history': [],
            'last_message': None
        }
    
    def add_message(self, message: Dict[str, Any]) -> bool:
        """Add a message to the queue and update agent status."""
        self.messages.append(message)
        self._update_agent_status(message)
        return True
    
    def get_queue_size(self) -> int:
        """Get total number of messages in the queue."""
        return len(self.messages)
    
    def clear_queue(self) -> None:
        """Clear all messages and reset all agent statuses."""
        self.messages.clear()
        self.agent_status.clear()
    
    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get current status and history for an agent, creating if needed."""
        return self.agent_status.get(agent_id, self._get_default_status())
    
    def get_agent_history(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all messages sent to an agent."""
        return [msg for msg in self.messages if msg['to_agent'] == agent_id]
    
    def clear_agent_messages(self, agent_id: str) -> None:
        """Clear all messages and reset status for an agent."""
        self.messages = [msg for msg in self.messages if msg['to_agent'] != agent_id]
        self.agent_status[agent_id] = self._get_default_status()
    
    def _update_agent_status(self, message: Dict[str, Any]) -> None:
        """Update agent status with a new message."""
        agent_id = message['to_agent']
        if agent_id not in self.agent_status:
            self.agent_status[agent_id] = self._get_default_status()
        
        self.agent_status[agent_id]['message_history'].append(message)
        self.agent_status[agent_id]['last_message'] = message

def send_message(
    phone_number: str,
    message: str,
    media_files: Optional[List[str]] = None,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Send an SMS or MMS message.
    
    Args:
        phone_number: Recipient's phone number
        message: Message text
        media_files: Optional list of media file paths
        config: Optional configuration dict
        
    Returns:
        Dict containing send status and any error messages
    """
    if not phone_number or not message:
        return {
            'success': False,
            'error': 'Phone number and message are required'
        }
    
    try:
        # TODO: Implement actual SMS/MMS sending logic
        # This is a placeholder implementation
        logger.info(f"Sending message to {phone_number}: {message}")
        if media_files:
            logger.info(f"With media files: {media_files}")
        
        return {
            'success': True,
            'message_id': 'placeholder_id',
            'sent_at': 'timestamp'
        }
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return {
            'success': False,
            'error': str(e)
        }

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

def parse_args() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Cell Phone Messaging CLI")
    parser.add_argument("--to", required=True, help="Recipient agent ID")
    parser.add_argument("--content", required=True, help="Message content")
    parser.add_argument("--mode", default="NORMAL", help="Message mode")
    parser.add_argument("--priority", type=int, default=0, help="Message priority")
    parser.add_argument("--from-agent", help="Sender agent ID")
    return parser.parse_args()

def validate_priority(priority: int) -> bool:
    """Validate message priority.
    
    Args:
        priority: Priority to validate
        
    Returns:
        True if valid, False otherwise
    """
    return 0 <= priority <= 5

def cli_main() -> None:
    """Run the CLI interface."""
    args = parse_args()
    phone = CellPhone()
    
    if not validate_priority(args.priority):
        logger.error("Invalid priority: %d", args.priority)
        return
        
    success = phone.send_message(
        to_agent=args.to,
        content=args.content,
        mode=args.mode,
        priority=args.priority,
        from_agent=args.from_agent
    )
    
    if success:
        logger.info("Message sent successfully")
    else:
        logger.error("Failed to send message") 