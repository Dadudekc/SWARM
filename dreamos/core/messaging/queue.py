"""
Message queue implementation for Dream.OS agent communication.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from .base import Message, MessageQueue, MessagePriority

logger = logging.getLogger("dreamos.messaging")

class AsyncMessageQueue(MessageQueue):
    """Asynchronous message queue implementation."""
    
    def __init__(self, max_size: Optional[int] = None):
        """Initialize queue.
        
        Args:
            max_size: Optional maximum queue size
        """
        self._queue = asyncio.PriorityQueue(maxsize=max_size)
        self._message_map: Dict[str, Message] = {}
        self._processing = False
        self._processing_task: Optional[asyncio.Task] = None
    
    async def enqueue(self, message: Message) -> bool:
        """Add a message to the queue.
        
        Args:
            message: Message to enqueue
            
        Returns:
            bool: True if message was enqueued successfully
        """
        try:
            # Store message in map
            self._message_map[message.id] = message
            
            # Add to queue with priority
            priority = (message.priority.value, message.timestamp)
            await self._queue.put((priority, message))
            
            logger.debug(f"Enqueued message {message.id} with priority {message.priority}")
            return True
            
        except Exception as e:
            logger.error(f"Error enqueueing message {message.id}: {e}")
            return False
    
    async def dequeue(self) -> Optional[Message]:
        """Get the next message from the queue.
        
        Returns:
            Optional[Message]: Next message or None if queue is empty
        """
        try:
            if self._queue.empty():
                return None
                
            _, message = await self._queue.get()
            
            # Remove from message map
            self._message_map.pop(message.id, None)
            
            logger.debug(f"Dequeued message {message.id}")
            return message
            
        except Exception as e:
            logger.error(f"Error dequeuing message: {e}")
            return None
    
    async def peek(self) -> Optional[Message]:
        """Peek at the next message without removing it.
        
        Returns:
            Optional[Message]: Next message or None if queue is empty
        """
        try:
            if self._queue.empty():
                return None
                
            # Peek at the next message
            message = self._queue._queue[0][1]
            return message
            
        except Exception as e:
            logger.error(f"Error peeking message: {e}")
            return None
    
    async def remove(self, message_id: str) -> bool:
        """Remove a message from the queue.
        
        Args:
            message_id: ID of message to remove
            
        Returns:
            bool: True if message was removed successfully
        """
        try:
            # Get message from map
            message = self._message_map.get(message_id)
            if not message:
                return False
            
            # Create new queue without the message
            new_queue = asyncio.PriorityQueue(maxsize=self._queue.maxsize)
            while not self._queue.empty():
                _, msg = await self._queue.get()
                if msg.id != message_id:
                    priority = (msg.priority.value, msg.timestamp)
                    await new_queue.put((priority, msg))
            
            # Replace old queue with new one
            self._queue = new_queue
            
            # Remove from message map
            self._message_map.pop(message_id, None)
            
            logger.debug(f"Removed message {message_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing message {message_id}: {e}")
            return False
    
    async def clear(self) -> None:
        """Clear all messages from the queue."""
        try:
            # Clear queue
            while not self._queue.empty():
                await self._queue.get()
            
            # Clear message map
            self._message_map.clear()
            
            logger.debug("Cleared all messages from queue")
            
        except Exception as e:
            logger.error(f"Error clearing queue: {e}")
    
    async def start_processing(self, handler: callable) -> None:
        """Start processing messages.
        
        Args:
            handler: Async function to handle messages
        """
        if self._processing:
            return
            
        self._processing = True
        
        async def process_loop():
            while self._processing:
                try:
                    message = await self.dequeue()
                    if message:
                        await handler(message)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                await asyncio.sleep(0.1)
        
        self._processing_task = asyncio.create_task(process_loop())
    
    async def stop_processing(self) -> None:
        """Stop processing messages."""
        self._processing = False
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
            self._processing_task = None
