"""
Message processor for Dream.OS.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, Callable, Awaitable
from .common import Message, MessageContext
from .enums import MessageMode, MessagePriority, MessageType

logger = logging.getLogger(__name__)

class MessageProcessor:
    """Handles message processing and routing."""
    
    def __init__(self, runtime_dir: str = "runtime"):
        """Initialize message processor.
        
        Args:
            runtime_dir: Directory for runtime files
        """
        self.runtime_dir = runtime_dir
        self.message_dir = os.path.join(runtime_dir, "messages")
        self.handlers: Dict[MessageMode, Callable[[Message], Awaitable[None]]] = {}
        self._running = False
        self._queue = asyncio.Queue()
        
        # Create directories
        os.makedirs(self.message_dir, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    async def start(self):
        """Start message processing."""
        if self._running:
            return
            
        self._running = True
        logger.info("Starting message processor")
        
        # Start message processing loop
        asyncio.create_task(self._process_messages())
    
    async def stop(self):
        """Stop message processing."""
        if not self._running:
            return
            
        self._running = False
        logger.info("Stopping message processor")
        
        # Wait for queue to empty
        if not self._queue.empty():
            logger.info("Waiting for message queue to empty...")
            await self._queue.join()
    
    def register_handler(self, mode: MessageMode, handler: Callable[[Message], Awaitable[None]]):
        """Register a message handler.
        
        Args:
            mode: Message mode to handle
            handler: Async handler function
        """
        self.handlers[mode] = handler
        logger.info(f"Registered handler for {mode.name} messages")
    
    def unregister_handler(self, mode: MessageMode):
        """Unregister a message handler.
        
        Args:
            mode: Message mode to unregister
        """
        if mode in self.handlers:
            del self.handlers[mode]
            logger.info(f"Unregistered handler for {mode.name} messages")
    
    async def send_message(self, message: Message):
        """Send a message for processing.
        
        Args:
            message: Message to send
        """
        if not message.validate():
            logger.error("Invalid message")
            return
            
        # Save message
        self._save_message(message)
        
        # Add to queue
        await self._queue.put(message)
        logger.info(f"Queued message {message.message_id}")
    
    async def _process_messages(self):
        """Process messages from queue."""
        while self._running:
            try:
                # Get message from queue
                message = await self._queue.get()
                
                try:
                    # Get handler for message mode
                    handler = self.handlers.get(message.type)
                    if handler:
                        # Process message
                        await handler(message)
                        logger.info(f"Processed message {message.message_id}")
                    else:
                        logger.warning(f"No handler for {message.type.name} messages")
                finally:
                    # Mark message as done
                    self._queue.task_done()
                    
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await asyncio.sleep(1)  # Prevent tight loop on error
    
    def _save_message(self, message: Message):
        """Save message to disk.
        
        Args:
            message: Message to save
        """
        try:
            # Create message file
            message_file = os.path.join(self.message_dir, f"{message.message_id}.json")
            
            # Save message data
            with open(message_file, "w") as f:
                f.write(message.to_dict())
                
        except Exception as e:
            logger.error(f"Error saving message: {e}")
    
    def _load_message(self, message_id: str) -> Optional[Message]:
        """Load message from disk.
        
        Args:
            message_id: Message ID to load
            
        Returns:
            Loaded message or None if not found
        """
        try:
            # Get message file
            message_file = os.path.join(self.message_dir, f"{message_id}.json")
            
            # Check if exists
            if not os.path.exists(message_file):
                return None
                
            # Load message data
            with open(message_file, "r") as f:
                data = f.read()
                return Message.from_dict(data)
                
        except Exception as e:
            logger.error(f"Error loading message: {e}")
            return None 
