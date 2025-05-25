"""
Processor Module

Handles message processing and delivery for the Dream.OS messaging system.
"""

import logging
import threading
import time
import os
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

from .message import Message, MessageMode
from .queue import MessageQueue

logger = logging.getLogger('messaging.processor')

class MessageProcessor:
    """Handles message processing and delivery."""
    
    def __init__(self, queue: Optional[MessageQueue] = None, base_path: Optional[str] = None):
        """Initialize the message processor.
        
        Args:
            queue: Optional message queue instance
            base_path: Optional base path for message storage
        """
        self.queue = queue or MessageQueue()
        self._running = False
        self._processing_thread: Optional[threading.Thread] = None
        self._handlers: Dict[MessageMode, List[Callable]] = {}
        self._default_handler: Optional[Callable] = None
        self.base_path = base_path or os.path.join(os.getcwd(), "messages")
        
        # Ensure base path exists
        os.makedirs(self.base_path, exist_ok=True)
        
        # Processing parameters
        self.retry_attempts = 3
        self.retry_delay = 5
        self.verification_delay = 0.2
        
    def start(self):
        """Start the message processor."""
        if self._running:
            return
            
        self._running = True
        self._processing_thread = threading.Thread(target=self._process_messages)
        self._processing_thread.daemon = True
        self._processing_thread.start()
        logger.info("Message processor started")
        
    def stop(self):
        """Stop the message processor."""
        self._running = False
        if self._processing_thread:
            self._processing_thread.join(timeout=5)
        logger.info("Message processor stopped")
        
    def register_handler(self, mode: MessageMode, handler: Callable):
        """Register a handler for a specific message mode.
        
        Args:
            mode: Message mode to handle
            handler: Handler function
        """
        if mode not in self._handlers:
            self._handlers[mode] = []
        self._handlers[mode].append(handler)
        logger.info(f"Registered handler for {mode.name}")
        
    def register_default_handler(self, handler: Callable):
        """Register a default message handler.
        
        Args:
            handler: Default handler function
        """
        self._default_handler = handler
        logger.info("Registered default handler")
        
    def send_message(self, message: Message) -> bool:
        """Send a message.
        
        Args:
            message: Message to send
            
        Returns:
            bool: True if message was successfully queued
        """
        try:
            if not message.validate():
                return False
                
            success = self.queue.enqueue(message)
            if success:
                logger.info(f"Message queued from {message.from_agent} to {message.to_agent}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
            
    def send_to_all(self, message: Message) -> Dict[str, bool]:
        """Send a message to all agents.
        
        Args:
            message: Message to send
            
        Returns:
            Dict mapping agent IDs to success status
        """
        results = {}
        for agent_id in self._get_all_agents():
            msg = Message(
                from_agent=message.from_agent,
                to_agent=agent_id,
                content=message.content,
                mode=message.mode,
                priority=message.priority,
                metadata=message.metadata
            )
            results[agent_id] = self.send_message(msg)
        return results
        
    def get_status(self) -> Dict[str, Any]:
        """Get current processor status.
        
        Returns:
            Dict containing processor statistics
        """
        try:
            return {
                'is_running': self._running,
                'queue_status': self.queue.get_status(),
                'handler_count': sum(len(handlers) for handlers in self._handlers.values())
            }
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return {'error': str(e)}
            
    def _process_messages(self):
        """Process messages in the queue."""
        while self._running:
            try:
                # Get next message
                message_data = self.queue.dequeue()
                if not message_data:
                    time.sleep(0.1)
                    continue
                    
                # Convert to Message object
                message = Message.from_dict(message_data)
                
                # Process message with retries
                success = False
                for attempt in range(self.retry_attempts):
                    try:
                        success = self._handle_message(message)
                        if success:
                            break
                        time.sleep(self.retry_delay)
                    except Exception as e:
                        logger.error(f"Error processing message (attempt {attempt + 1}): {e}")
                        if attempt < self.retry_attempts - 1:
                            time.sleep(self.retry_delay)
                            
            except Exception as e:
                logger.error(f"Error in message processing loop: {e}")
                time.sleep(1)  # Back off on error
                
    def _handle_message(self, message: Message) -> bool:
        """Handle a message using registered handlers.
        
        Args:
            message: Message to handle
            
        Returns:
            bool: True if message was successfully handled
        """
        try:
            # Get handlers for message mode
            handlers = self._handlers.get(message.mode, [])
            
            # If no specific handlers, use default
            if not handlers and self._default_handler:
                handlers = [self._default_handler]
                
            # Execute handlers
            success = True
            for handler in handlers:
                try:
                    handler_result = handler(message)
                    if handler_result is False:
                        success = False
                        break
                except Exception as e:
                    logger.error(f"Handler error: {e}")
                    success = False
                    break
                    
            return success
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return False
            
    def _get_all_agents(self) -> List[str]:
        """Get list of all agent IDs.
        
        Returns:
            List of agent IDs
        """
        # TODO: Implement agent discovery
        return ["Agent-1", "Agent-2"]  # Placeholder 