"""Message processing module for handling agent communications."""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from pathlib import Path

from ..utils.file_utils import atomic_write
from dreamos.social.utils.log_manager import LogManager

logger = logging.getLogger(__name__)

class MessageProcessor:
    """Handles message processing and routing between agents."""
    
    def __init__(self, runtime_dir: str):
        """Initialize message processor.
        
        Args:
            runtime_dir: Runtime directory for message storage
        """
        self.runtime_dir = Path(runtime_dir)
        self.inbox_path = self.runtime_dir / "inbox.json"
        self.outbox_path = self.runtime_dir / "outbox.json"
        self.logger = LogManager()
        self._handlers: Dict[str, List[Callable]] = {}
        self._running = False
        self._queue = asyncio.Queue()
        
        # Ensure directories exist
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        
    async def start(self) -> None:
        """Start the message processor."""
        if self._running:
            return
            
        self._running = True
        asyncio.create_task(self._process_messages())
        logger.info("Message processor started")
        
    async def stop(self) -> None:
        """Stop the message processor."""
        if not self._running:
            return
            
        self._running = False
        await self._queue.join()
        logger.info("Message processor stopped")
        
    def register_handler(self, message_type: str, handler: Callable) -> None:
        """Register a handler for a message type.
        
        Args:
            message_type: Type of message to handle
            handler: Handler function to call
        """
        if message_type not in self._handlers:
            self._handlers[message_type] = []
        self._handlers[message_type].append(handler)
        logger.debug(f"Registered handler for {message_type}")
        
    def unregister_handler(self, message_type: str, handler: Callable) -> None:
        """Unregister a handler for a message type.
        
        Args:
            message_type: Type of message
            handler: Handler function to remove
        """
        if message_type in self._handlers:
            self._handlers[message_type].remove(handler)
            if not self._handlers[message_type]:
                del self._handlers[message_type]
            logger.debug(f"Unregistered handler for {message_type}")
            
    async def send_message(self, message: Dict[str, Any]) -> None:
        """Send a message to be processed.
        
        Args:
            message: Message to send
        """
        message['timestamp'] = datetime.utcnow().isoformat()
        await self._queue.put(message)
        logger.debug(f"Queued message: {message.get('type', 'unknown')}")
        
    async def _process_messages(self) -> None:
        """Process messages from the queue."""
        while self._running:
            try:
                message = await self._queue.get()
                message_type = message.get('type')
                
                if message_type in self._handlers:
                    for handler in self._handlers[message_type]:
                        try:
                            await handler(message)
                        except Exception as e:
                            logger.error(f"Error in message handler: {e}")
                else:
                    logger.warning(f"No handlers for message type: {message_type}")
                    
            except Exception as e:
                logger.error(f"Error processing message: {e}")
            finally:
                self._queue.task_done()
                # Clear the queue after processing
                while not self._queue.empty():
                    try:
                        self._queue.get_nowait()
                        self._queue.task_done()
                    except asyncio.QueueEmpty:
                        break
                
    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcast a message to all handlers.
        
        Args:
            message: Message to broadcast
        """
        message['type'] = 'broadcast'
        await self.send_message(message)
        
    def get_queue_size(self) -> int:
        """Get current queue size.
        
        Returns:
            Number of messages in queue
        """
        return self._queue.qsize()
        
    def is_running(self) -> bool:
        """Check if processor is running.
        
        Returns:
            True if running
        """
        return self._running 