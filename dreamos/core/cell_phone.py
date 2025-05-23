"""
Cell Phone Interface

Provides a cell phone interface for agent communication.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from .persistent_queue import PersistentQueue
from agent_tools.utils.init_mailbox import AgentMailbox

logger = logging.getLogger('cell_phone')

class MessageMode(Enum):
    """Message modes for different types of communication."""
    RESUME = "[RESUME]"
    SYNC = "[SYNC]"
    VERIFY = "[VERIFY]"
    REPAIR = "[REPAIR]"
    BACKUP = "[BACKUP]"
    RESTORE = "[RESTORE]"
    CLEANUP = "[CLEANUP]"
    CAPTAIN = "[CAPTAIN]"
    TASK = "[TASK]"
    INTEGRATE = "[INTEGRATE]"
    NORMAL = ""  # No additional tags

@dataclass
class Message:
    """Represents a cell phone message with metadata."""
    from_agent: str
    to_agent: str
    content: str
    priority: int
    timestamp: datetime
    status: str = "queued"

class CellPhone:
    """Singleton class managing cell phone communication between agents."""
    
    _instance: Optional['CellPhone'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the cell phone interface."""
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.queue = PersistentQueue()
            self.message_history = []
            logger.info("Cell phone interface initialized")
    
    def send_message(self, from_agent: str, to_agent: str, message: str, priority: int = 0, mode: MessageMode = MessageMode.NORMAL) -> bool:
        """Send a message to an agent.
        
        Args:
            from_agent: The sender agent ID
            to_agent: The recipient agent ID
            message: The message content
            priority: Message priority (0-5)
            mode: The message mode
            
        Returns:
            bool: True if message was successfully queued
            
        Raises:
            ValueError: If priority is invalid or message is empty
        """
        if not message:
            raise ValueError("Message cannot be empty")
        if not 0 <= priority <= 5:
            raise ValueError("Priority must be between 0 and 5")
            
        try:
            msg = {
                "from_agent": from_agent,
                "to_agent": to_agent,
                "content": f"{mode.value} {message}" if mode != MessageMode.NORMAL else message,
                "priority": priority,
                "timestamp": datetime.now().isoformat(),
                "status": "queued"
            }
            
            success = self.queue.enqueue(msg)
            if success:
                self.message_history.append(msg)
                logger.info(f"Message queued from {from_agent} to {to_agent}")
            return success
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current message queue status.
        
        Returns:
            Dict containing queue statistics and message history
        """
        status = self.queue.get_status()
        status.update({
            "message_history": self.message_history,
            "last_message": self.message_history[-1] if self.message_history else None
        })
        return status
    
    def clear_messages(self, agent_id: Optional[str] = None) -> None:
        """Clear messages from the queue.
        
        Args:
            agent_id: Optional agent ID to clear messages for. If None, clears all messages.
        """
        if agent_id:
            self.queue.clear_agent(agent_id)
            self.message_history = [msg for msg in self.message_history if msg["to_agent"] != agent_id]
            logger.info(f"Messages cleared for {agent_id}")
        else:
            self.queue.clear()
            self.message_history = []
            logger.info("All messages cleared")
    
    def shutdown(self) -> None:
        """Clean up resources."""
        self.queue.shutdown()
        logger.info("Cell phone interface shut down")

def send_message(to_agent: str, message: str, priority: int = 0, mode: MessageMode = MessageMode.NORMAL) -> bool:
    """Send a message to an agent using the cell phone interface.
    
    Args:
        to_agent: The recipient agent ID
        message: The message content
        priority: Message priority (0-5)
        mode: The message mode
        
    Returns:
        bool: True if message was successfully queued
        
    Raises:
        ValueError: If priority is invalid or message is empty
    """
    cell_phone = CellPhone()
    return cell_phone.send_message("CLI", to_agent, message, priority, mode) 