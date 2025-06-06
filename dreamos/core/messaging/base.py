"""
Base classes for messaging components.
"""

import asyncio
import logging
from typing import Dict, Set, Callable, Pattern, Optional, Any
from queue import PriorityQueue
import re
from abc import ABC, abstractmethod
from datetime import datetime

logger = logging.getLogger('dreamos.messaging')

class BaseMessagingComponent:
    """Base class for messaging components with common functionality."""
    
    def __init__(self):
        """Initialize base messaging component."""
        self._subscribers: Dict[str, Set[Callable]] = {}
        self._pattern_subscribers: Dict[Pattern, Set[Callable]] = {}
        self._message_queue: PriorityQueue = PriorityQueue()
        self._processing = False
    
    async def subscribe(self, topic: str, handler: Callable) -> None:
        """Subscribe to a topic.
        
        Args:
            topic: Topic to subscribe to
            handler: Callback function to handle messages
        """
        try:
            if topic not in self._subscribers:
                self._subscribers[topic] = set()
            self._subscribers[topic].add(handler)
        except Exception as e:
            logger.error(f"Error subscribing to topic {topic}: {e}")
    
    async def subscribe_pattern(self, pattern: str, handler: Callable) -> None:
        """Subscribe to messages matching a pattern.
        
        Args:
            pattern: Regex pattern to match
            handler: Callback function to handle messages
        """
        try:
            compiled_pattern = re.compile(pattern)
            if compiled_pattern not in self._pattern_subscribers:
                self._pattern_subscribers[compiled_pattern] = set()
            self._pattern_subscribers[compiled_pattern].add(handler)
        except Exception as e:
            logger.error(f"Error subscribing to pattern {pattern}: {e}")
    
    async def unsubscribe(self, topic: str, handler: Callable) -> None:
        """Unsubscribe from a topic.
        
        Args:
            topic: Topic to unsubscribe from
            handler: Handler to remove
        """
        try:
            if topic in self._subscribers:
                self._subscribers[topic].discard(handler)
                if not self._subscribers[topic]:
                    del self._subscribers[topic]
        except Exception as e:
            logger.error(f"Error unsubscribing from topic {topic}: {e}")
    
    async def unsubscribe_pattern(self, pattern: str, handler: Callable) -> None:
        """Unsubscribe from a pattern.
        
        Args:
            pattern: Pattern to unsubscribe from
            handler: Handler to remove
        """
        try:
            compiled_pattern = re.compile(pattern)
            if compiled_pattern in self._pattern_subscribers:
                self._pattern_subscribers[compiled_pattern].discard(handler)
                if not self._pattern_subscribers[compiled_pattern]:
                    del self._pattern_subscribers[compiled_pattern]
        except Exception as e:
            logger.error(f"Error unsubscribing from pattern {pattern}: {e}")
    
    async def start_processing(self) -> None:
        """Start processing the message queue."""
        self._processing = True
        while self._processing:
            try:
                _, message = self._message_queue.get_nowait()
                await self._process_message(message)
            except asyncio.QueueEmpty:
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
    
    async def stop_processing(self) -> None:
        """Stop processing the message queue."""
        self._processing = False
    
    async def _process_message(self, message: Any) -> None:
        """Process a single message.
        
        Args:
            message: Message to process
        """
        raise NotImplementedError("Subclasses must implement _process_message")
    
    async def _notify_subscribers(self, message: Any) -> None:
        """Notify subscribers of a new message.
        
        Args:
            message: Message to notify about
        """
        # Notify direct subscribers
        if hasattr(message, 'to_agent') and message.to_agent in self._subscribers:
            for handler in self._subscribers[message.to_agent]:
                try:
                    await handler(message)
                except Exception as e:
                    logger.error(f"Error in subscriber handler: {e}")
        
        # Notify pattern subscribers
        for pattern, handlers in self._pattern_subscribers.items():
            if hasattr(message, 'to_agent') and pattern.match(message.to_agent):
                for handler in handlers:
                    try:
                        await handler(message)
                    except Exception as e:
                        logger.error(f"Error in pattern subscriber handler: {e}")

class BaseMessageHandler(ABC):
    """Base class for message handlers."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the message handler.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
    @abstractmethod
    async def handle_message(self, message: Any) -> bool:
        """Handle an incoming message.
        
        Args:
            message: The message to handle
            
        Returns:
            bool: True if message was handled successfully
        """
        pass
    
    @abstractmethod
    async def send_message(self, message: Any) -> bool:
        """Send a message.
        
        Args:
            message: The message to send
            
        Returns:
            bool: True if message was sent successfully
        """
        pass
    
    @abstractmethod
    def validate_message(self, message: Any) -> bool:
        """Validate a message.
        
        Args:
            message: The message to validate
            
        Returns:
            bool: True if message is valid
        """
        pass 