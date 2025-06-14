"""
Message handler implementation for Dream.OS agent communication.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Set, Callable, Any
from datetime import datetime
from .base import Message, MessageHandler, MessageType, MessagePriority

logger = logging.getLogger("dreamos.messaging")

class MessageProcessor(MessageHandler):
    """Processor for handling messages."""
    
    def __init__(self):
        """Initialize processor."""
        self._handlers: Dict[MessageType, List[Callable]] = {}  # message type -> list of handlers
        self._default_handler: Optional[Callable] = None
        self._error_handler: Optional[Callable] = None
        self._processing = False
        self._processing_task: Optional[asyncio.Task] = None
        self._message_queue: asyncio.Queue = asyncio.Queue()
    
    def add_handler(self, message_type: MessageType, handler: Callable) -> None:
        """Add a handler for a message type.
        
        Args:
            message_type: Type of message to handle
            handler: Function to handle messages of this type
        """
        if message_type not in self._handlers:
            self._handlers[message_type] = []
        self._handlers[message_type].append(handler)
        logger.debug(f"Added handler for message type {message_type}")
    
    def remove_handler(self, message_type: MessageType, handler: Callable) -> None:
        """Remove a handler for a message type.
        
        Args:
            message_type: Type of message to remove handler for
            handler: Handler function to remove
        """
        if message_type in self._handlers:
            self._handlers[message_type].remove(handler)
            if not self._handlers[message_type]:
                del self._handlers[message_type]
            logger.debug(f"Removed handler for message type {message_type}")
    
    def set_default_handler(self, handler: Optional[Callable]) -> None:
        """Set the default message handler.
        
        Args:
            handler: Function to handle unhandled message types
        """
        self._default_handler = handler
        logger.debug("Set default message handler")
    
    def set_error_handler(self, handler: Optional[Callable]) -> None:
        """Set the error handler.
        
        Args:
            handler: Function to handle processing errors
        """
        self._error_handler = handler
        logger.debug("Set error handler")
    
    async def handle(self, message: Message) -> bool:
        """Handle a message.
        
        Args:
            message: Message to handle
            
        Returns:
            bool: True if message was handled successfully
        """
        try:
            # Get handlers for message type
            handlers = self._handlers.get(message.type, [])
            if not handlers and self._default_handler:
                handlers = [self._default_handler]
            
            if not handlers:
                logger.warning(f"No handlers found for message type {message.type}")
                return False
            
            # Call all handlers
            success = True
            for handler in handlers:
                try:
                    result = await handler(message)
                    if not result:
                        success = False
                except Exception as e:
                    logger.error(f"Error in handler for message {message.id}: {e}")
                    if self._error_handler:
                        await self._error_handler(message, e)
                    success = False
            
            logger.debug(f"Handled message {message.id} with {len(handlers)} handlers")
            return success
            
        except Exception as e:
            logger.error(f"Error handling message {message.id}: {e}")
            if self._error_handler:
                await self._error_handler(message, e)
            return False
    
    async def process(self, message: Message) -> None:
        """Add a message to the processing queue.
        
        Args:
            message: Message to process
        """
        await self._message_queue.put(message)
        logger.debug(f"Added message {message.id} to processing queue")
    
    async def start(self) -> None:
        """Start processing messages."""
        if self._processing:
            return
            
        self._processing = True
        
        async def process_loop():
            while self._processing:
                try:
                    message = await self._message_queue.get()
                    await self.handle(message)
                    self._message_queue.task_done()
                except Exception as e:
                    logger.error(f"Error in message processing loop: {e}")

                # Yield control **only** when the queue is empty so we do not
                # introduce unnecessary latency while messages are waiting to
                # be processed (fixes flaky timing-based tests).
                if self._message_queue.empty():
                    # A very short sleep is enough to yield to the event-loop
                    # without noticeably delaying delivery.
                    await asyncio.sleep(0.01)
        
        self._processing_task = asyncio.create_task(process_loop())
        logger.info("Started message processor")
    
    async def stop(self) -> None:
        """Stop processing messages."""
        self._processing = False
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
            self._processing_task = None
        logger.info("Stopped message processor")
    
    async def wait_empty(self) -> None:
        """Wait for message queue to be empty."""
        await self._message_queue.join()
        logger.debug("Message queue is empty")
    
    def is_processing(self) -> bool:
        """Check if processor is running.
        
        Returns:
            bool: True if processor is running
        """
        return self._processing
    
    def queue_size(self) -> int:
        """Get current queue size.
        
        Returns:
            int: Number of messages in queue
        """
        return self._message_queue.qsize() 