"""
Unified message system implementation for Dream.OS agent communication.
"""

import logging
import uuid
from typing import Dict, List, Optional, Set, Callable, Any
from datetime import datetime
from .base import Message, MessageType, MessagePriority
from .queue import AsyncMessageQueue
from .router import AgentMessageRouter
from .validator import MessageValidator
from .handler import MessageProcessor

logger = logging.getLogger("dreamos.messaging")

class MessageSystem:
    """Unified message system for agent communication."""
    
    def __init__(self):
        """Initialize message system."""
        self._queue = AsyncMessageQueue()
        self._router = AgentMessageRouter()
        self._validator = MessageValidator()
        self._processor = MessageProcessor()
        
        # Set up default error handler
        self._processor.set_error_handler(self._handle_error)
    
    async def start(self) -> None:
        """Start the message system."""
        await self._processor.start()
        logger.info("Started message system")
    
    async def stop(self) -> None:
        """Stop the message system."""
        await self._processor.stop()
        logger.info("Stopped message system")
    
    async def send(self, message: Message) -> bool:
        """Send a message through the system.
        
        Args:
            message: Message to send
            
        Returns:
            bool: True if message was sent successfully
        """
        try:
            # Validate message
            is_valid, error = await self._validator.validate(message)
            if not is_valid:
                logger.error(f"Message validation failed: {error}")
                return False
            
            # Route message
            if not await self._router.route(message):
                logger.error(f"Message routing failed for {message.id}")
                return False
            
            # Add to queue
            if not await self._queue.enqueue(message):
                logger.error(f"Failed to enqueue message {message.id}")
                return False
            
            # Process message
            await self._processor.process(message)
            
            logger.debug(f"Message {message.id} sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error sending message {message.id}: {e}")
            return False
    
    async def broadcast(self, message: Message, exclude: Optional[Set[str]] = None) -> int:
        """Broadcast a message to all agents except *exclude* by cloning the provided
        message for each recipient and sending it through the regular ``send`` pipeline.
        """
        try:
            exclude = exclude or set()

            # Build a recipient set from the router configuration (union of all allowed recipients)
            recipients: Set[str] = set()
            for allowed in self._router._routes.values():  # pylint: disable=protected-access
                recipients.update(allowed)

            recipients -= exclude

            success_count = 0
            for recipient in recipients:
                msg_copy = message.copy()
                msg_copy.recipient = recipient
                if await self.send(msg_copy):
                    success_count += 1

            logger.debug(
                "Broadcast message %s to %d recipients (excluded=%s)",
                message.id,
                success_count,
                exclude,
            )
            return success_count
        except Exception as exc:  # noqa: B902
            logger.error("Error broadcasting message %s: %s", message.id, exc)
            return 0
    
    def add_route(self, agent_id: str, allowed_recipients: Set[str]) -> None:
        """Add routing rules for an agent.
        
        Args:
            agent_id: ID of agent to add routes for
            allowed_recipients: Set of agent IDs this agent can send to
        """
        self._router.add_route(agent_id, allowed_recipients)
    
    def remove_route(self, agent_id: str) -> None:
        """Remove routing rules for an agent.
        
        Args:
            agent_id: ID of agent to remove routes for
        """
        self._router.remove_route(agent_id)
    
    def add_handler(self, message_type: MessageType, handler: Callable) -> None:
        """Register a handler for a given message type on BOTH the router (synchronous path)
        and the processor (queued path). This ensures that handlers registered via the public
        API are invoked regardless of whether the message is delivered directly via routing
        (e.g. broadcasts) or later consumed from the async processing queue.
        """
        self._processor.add_handler(message_type, handler)
    
    def remove_handler(self, message_type: MessageType, handler: Callable) -> None:
        """Remove an existing handler from both the router and processor registries."""
        self._processor.remove_handler(message_type, handler)
    
    def set_default_handler(self, handler: Optional[Callable]) -> None:
        """Register the default handler on both router and processor so unrecognised message
        types are handled consistently."""
        self._processor.set_default_handler(handler)
    
    def set_rate_limit(self, agent_id: str, max_messages: int, time_window) -> None:
        """Set rate limit for an agent.
        
        This helper accepts either an ``int``/``float`` representing seconds or a
        ``datetime.timedelta`` instance, forwarding a ``timedelta`` to the underlying
        validator.
        """
        from datetime import timedelta
        if isinstance(time_window, (int, float)):
            time_window = timedelta(seconds=time_window)
        self._validator.set_rate_limit(agent_id, max_messages, time_window)
    
    def set_content_pattern(self, message_type: MessageType, pattern: str) -> None:
        """Set content validation pattern for a message type.
        
        Args:
            message_type: Type of message to set pattern for
            pattern: Regex pattern for content validation
        """
        self._validator.set_content_pattern(message_type, pattern)
    
    def set_required_fields(self, message_type: MessageType, fields: Set[str]) -> None:
        """Set required fields for a message type.
        
        Args:
            message_type: Type of message to set fields for
            fields: Set of required field names
        """
        self._validator.set_required_fields(message_type, fields)
    
    async def _handle_error(self, message: Message, error: Exception) -> None:
        """Handle message processing errors.
        
        Args:
            message: Message that caused the error
            error: Error that occurred
        """
        logger.error(f"Error processing message {message.id}: {error}")
        
        # Create error response
        error_message = Message(
            id=str(uuid.uuid4()),
            type=MessageType.ERROR,
            priority=MessagePriority.HIGH,
            sender="system",
            recipient=message.sender,
            content=str(error),
            metadata={
                "original_message_id": message.id,
                "error_type": type(error).__name__,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Send error response
        await self.send(error_message)
    
    @property
    def queue_size(self) -> int:
        """Get current queue size.
        
        Returns:
            int: Number of messages in queue
        """
        return self._processor.queue_size()
    
    @property
    def is_processing(self) -> bool:
        """Check if system is processing messages.
        
        Returns:
            bool: True if system is processing messages
        """
        return self._processor.is_processing() 