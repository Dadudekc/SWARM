"""
Message Router Implementation
---------------------------
Provides message routing functionality for the unified message system.
"""

import logging
import re
from typing import Dict, Set, Callable, Pattern, Optional
from .common import Message, MessageMode
from .unified_message_system import MessageRouter

logger = logging.getLogger('dreamos.messaging.router')

class MessageRouter(MessageRouter):
    """Message router implementation."""
    
    def __init__(self):
        """Initialize router."""
        # Direct routing rules
        self._routes: Dict[str, Set[str]] = {}
        
        # Pattern-based routing rules
        self._pattern_routes: Dict[Pattern, Set[str]] = {}
        
        # Mode-specific handlers
        self._mode_handlers: Dict[MessageMode, Set[Callable]] = {}
        
        # Default handlers
        self._default_handlers: Set[Callable] = set()
    
    async def route(self, message: Message) -> bool:
        """Route a message to its destination.
        
        Args:
            message: Message to route
            
        Returns:
            bool: True if message was successfully routed
        """
        try:
            # Get target agents
            targets = self._get_targets(message)
            if not targets:
                logger.warning(f"No targets found for message {message.message_id}")
                return False
            
            # Process message for each target
            success = True
            for target in targets:
                if not await self._process_for_target(message, target):
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Error routing message {message.message_id}: {e}")
            return False
    
    def _get_targets(self, message: Message) -> Set[str]:
        """Get target agents for a message.
        
        Args:
            message: Message to get targets for
            
        Returns:
            Set[str]: Set of target agent IDs
        """
        targets = set()
        
        # Check direct routes
        if message.to_agent in self._routes:
            targets.update(self._routes[message.to_agent])
        
        # Check pattern routes
        for pattern, route_targets in self._pattern_routes.items():
            if pattern.match(message.to_agent):
                targets.update(route_targets)
        
        # If no routes found, use recipient directly
        if not targets:
            targets.add(message.to_agent)
        
        return targets
    
    async def _process_for_target(self, message: Message, target: str) -> bool:
        """Process a message for a specific target.
        
        Args:
            message: Message to process
            target: Target agent ID
            
        Returns:
            bool: True if message was successfully processed
        """
        try:
            # Get handlers for message mode
            handlers = self._mode_handlers.get(message.mode, set())
            
            # Add default handlers if no mode-specific handlers
            if not handlers:
                handlers = self._default_handlers
            
            # Process with each handler
            success = True
            for handler in handlers:
                try:
                    if not await handler(message, target):
                        success = False
                except Exception as e:
                    logger.error(f"Error in handler for message {message.message_id}: {e}")
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing message {message.message_id} for {target}: {e}")
            return False
    
    def add_route(self, source: str, target: str) -> None:
        """Add a direct routing rule.
        
        Args:
            source: Source agent ID
            target: Target agent ID
        """
        if source not in self._routes:
            self._routes[source] = set()
        self._routes[source].add(target)
        logger.info(f"Added route from {source} to {target}")
    
    def add_pattern_route(self, pattern: str, target: str) -> None:
        """Add a pattern-based routing rule.
        
        Args:
            pattern: Regex pattern to match
            target: Target agent ID
        """
        compiled_pattern = re.compile(pattern)
        if compiled_pattern not in self._pattern_routes:
            self._pattern_routes[compiled_pattern] = set()
        self._pattern_routes[compiled_pattern].add(target)
        logger.info(f"Added pattern route {pattern} to {target}")
    
    def add_mode_handler(self, mode: MessageMode, handler: Callable) -> None:
        """Add a handler for a specific message mode.
        
        Args:
            mode: Message mode to handle
            handler: Handler function
        """
        if mode not in self._mode_handlers:
            self._mode_handlers[mode] = set()
        self._mode_handlers[mode].add(handler)
        logger.info(f"Added handler for mode {mode}")
    
    def add_default_handler(self, handler: Callable) -> None:
        """Add a default message handler.
        
        Args:
            handler: Handler function
        """
        self._default_handlers.add(handler)
        logger.info("Added default handler")
    
    def remove_route(self, source: str, target: str) -> None:
        """Remove a direct routing rule.
        
        Args:
            source: Source agent ID
            target: Target agent ID
        """
        if source in self._routes:
            self._routes[source].discard(target)
            if not self._routes[source]:
                del self._routes[source]
            logger.info(f"Removed route from {source} to {target}")
    
    def remove_pattern_route(self, pattern: str, target: str) -> None:
        """Remove a pattern-based routing rule.
        
        Args:
            pattern: Regex pattern to match
            target: Target agent ID
        """
        compiled_pattern = re.compile(pattern)
        if compiled_pattern in self._pattern_routes:
            self._pattern_routes[compiled_pattern].discard(target)
            if not self._pattern_routes[compiled_pattern]:
                del self._pattern_routes[compiled_pattern]
            logger.info(f"Removed pattern route {pattern} to {target}")
    
    def remove_mode_handler(self, mode: MessageMode, handler: Callable) -> None:
        """Remove a handler for a specific message mode.
        
        Args:
            mode: Message mode
            handler: Handler function to remove
        """
        if mode in self._mode_handlers:
            self._mode_handlers[mode].discard(handler)
            if not self._mode_handlers[mode]:
                del self._mode_handlers[mode]
            logger.info(f"Removed handler for mode {mode}")
    
    def remove_default_handler(self, handler: Callable) -> None:
        """Remove a default message handler.
        
        Args:
            handler: Handler function to remove
        """
        self._default_handlers.discard(handler)
        logger.info("Removed default handler")
    
    def get_routes(self) -> Dict[str, Set[str]]:
        """Get all direct routing rules.
        
        Returns:
            Dict[str, Set[str]]: Mapping of source to target agents
        """
        return self._routes.copy()
    
    def get_pattern_routes(self) -> Dict[str, Set[str]]:
        """Get all pattern-based routing rules.
        
        Returns:
            Dict[str, Set[str]]: Mapping of patterns to target agents
        """
        return {
            pattern.pattern: targets
            for pattern, targets in self._pattern_routes.items()
        }
    
    def get_mode_handlers(self) -> Dict[MessageMode, Set[Callable]]:
        """Get all mode-specific handlers.
        
        Returns:
            Dict[MessageMode, Set[Callable]]: Mapping of modes to handlers
        """
        return self._mode_handlers.copy()
    
    def get_default_handlers(self) -> Set[Callable]:
        """Get all default handlers.
        
        Returns:
            Set[Callable]: Set of default handlers
        """
        return self._default_handlers.copy() 
