"""
Message router implementation for Dream.OS agent communication.
"""

import logging
from typing import Dict, List, Optional, Set, Callable
from .base import Message, MessageRouter, MessageType

logger = logging.getLogger("dreamos.messaging")

class AgentMessageRouter(MessageRouter):
    """Router for handling message routing between agents."""
    
    def __init__(self):
        """Initialize router."""
        self._routes: Dict[str, Set[str]] = {}  # agent_id -> set of allowed recipients
        self._handlers: Dict[MessageType, List[Callable]] = {}  # message type -> list of handlers
        self._default_handler: Optional[Callable] = None
    
    def add_route(self, agent_id: str, allowed_recipients: Set[str]) -> None:
        """Add routing rules for an agent.
        
        Args:
            agent_id: ID of agent to add routes for
            allowed_recipients: Set of agent IDs this agent can send to
        """
        self._routes[agent_id] = allowed_recipients
        logger.debug(f"Added routes for agent {agent_id}: {allowed_recipients}")
    
    def remove_route(self, agent_id: str) -> None:
        """Remove routing rules for an agent.
        
        Args:
            agent_id: ID of agent to remove routes for
        """
        self._routes.pop(agent_id, None)
        logger.debug(f"Removed routes for agent {agent_id}")
    
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
    
    async def route(self, message: Message) -> bool:
        """Route a message to appropriate handlers.
        
        Args:
            message: Message to route
            
        Returns:
            bool: True if message was routed successfully
        """
        try:
            # Check routing rules
            if message.sender in self._routes:
                allowed = self._routes[message.sender]
                if message.recipient not in allowed:
                    logger.warning(
                        f"Message {message.id} blocked: {message.sender} not allowed to send to {message.recipient}"
                    )
                    return False
            
            # Get handlers for message type
            handlers = self._handlers.get(message.type, [])
            if not handlers and self._default_handler:
                handlers = [self._default_handler]
            
            if not handlers:
                logger.warning(f"No handlers found for message type {message.type}")
                return False
            
            # Call all handlers
            for handler in handlers:
                try:
                    await handler(message)
                except Exception as e:
                    logger.error(f"Error in handler for message {message.id}: {e}")
            
            logger.debug(f"Routed message {message.id} to {len(handlers)} handlers")
            return True
            
        except Exception as e:
            logger.error(f"Error routing message {message.id}: {e}")
            return False
    
    async def broadcast(self, message: Message, exclude: Optional[Set[str]] = None) -> int:
        """Broadcast a message to all agents except excluded ones.
        
        Args:
            message: Message to broadcast
            exclude: Optional set of agent IDs to exclude
            
        Returns:
            int: Number of successful broadcasts
        """
        try:
            exclude = exclude or set()
            success_count = 0
            
            # Get all possible recipients
            all_recipients = set()
            for recipients in self._routes.values():
                all_recipients.update(recipients)
            
            # Remove excluded recipients
            recipients = all_recipients - exclude
            
            # Route message to each recipient
            for recipient in recipients:
                message_copy = message.copy()
                message_copy.recipient = recipient
                if await self.route(message_copy):
                    success_count += 1
            
            logger.debug(f"Broadcast message {message.id} to {success_count} recipients")
            return success_count
            
        except Exception as e:
            logger.error(f"Error broadcasting message {message.id}: {e}")
            return 0 
