"""
Agent Cellphone Module

Provides direct message injection capabilities for agents.
"""

import asyncio
import logging
from typing import Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class AgentCellphone:
    """Handles direct message injection to agents."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the cellphone.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        
    async def send_message(self, 
                          agent_id: str,
                          message: str,
                          priority: int = 1) -> bool:
        """Send a message directly to an agent.
        
        Args:
            agent_id: Target agent ID
            message: Message to send
            priority: Message priority (1-5)
            
        Returns:
            True if message was queued successfully
        """
        try:
            await self.message_queue.put({
                "agent_id": agent_id,
                "message": message,
                "priority": priority,
                "timestamp": datetime.now().isoformat()
            })
            return True
        except Exception as e:
            logger.error(f"Error sending message to agent {agent_id}: {e}")
            return False
            
    async def process_messages(self):
        """Process queued messages."""
        while True:
            try:
                message = await self.message_queue.get()
                # TODO: Implement actual message injection
                # For now, just log the message
                logger.info(f"Injecting message to {message['agent_id']}: {message['message']}")
            except Exception as e:
                logger.error(f"Error processing message: {e}")
            finally:
                self.message_queue.task_done() 