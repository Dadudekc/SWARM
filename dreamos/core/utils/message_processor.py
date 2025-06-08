"""
Message Processor Module

Handles message routing and processing between agents.
"""

import asyncio
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class MessageProcessor:
    """Processes and routes messages between agents."""
    
    def __init__(self):
        """Initialize the message processor."""
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.handlers: Dict[str, callable] = {}
        
    async def send_message(self, message: Dict) -> bool:
        """Send a message to the queue.
        
        Args:
            message: Message dictionary to send
            
        Returns:
            True if message was queued successfully
        """
        try:
            await self.message_queue.put(message)
            return True
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
            
    async def register_handler(self, message_type: str, handler: callable):
        """Register a message handler.
        
        Args:
            message_type: Type of message to handle
            handler: Handler function to call
        """
        self.handlers[message_type] = handler
        
    async def process_messages(self):
        """Process messages from the queue."""
        while True:
            try:
                message = await self.message_queue.get()
                message_type = message.get("type")
                
                if message_type in self.handlers:
                    await self.handlers[message_type](message)
                else:
                    logger.warning(f"No handler for message type: {message_type}")
                    
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                
            finally:
                self.message_queue.task_done() 