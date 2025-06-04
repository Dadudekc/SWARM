"""
AgentBus - A legacy message bus implementation for agent communication.

.. deprecated:: 1.0
   Use :mod:`dreamos.core.messaging.unified_message_system` instead.

This module provided a centralized bus allowing agents to publish and subscribe
to messages in a decoupled manner and supported swarm-like behavior through
advanced routing and pattern matching. It is retained for backward
compatibility but no longer used by the core system.
"""

from typing import Any, Callable, Dict, List, Optional, Set, Pattern
from dataclasses import dataclass
from datetime import datetime
import asyncio
import logging
import re
from uuid import uuid4
from queue import PriorityQueue
from pathlib import Path
import json

from .common import Message, MessageMode, MessagePriority
from .base import BaseMessagingComponent

logger = logging.getLogger(__name__)


@dataclass
class BusMessage:
    """Represents a message in the agent bus system."""
    id: str
    topic: str
    content: Any
    sender: str
    timestamp: datetime
    metadata: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    pattern: Optional[str] = None
    mode: MessageMode = MessageMode.NORMAL

class AgentBus(BaseMessagingComponent):
    """
    A message bus implementation for agent communication with swarm support.
    
    This class provides a centralized message bus that allows agents to:
    - Publish messages to specific topics
    - Subscribe to topics and receive messages
    - Unsubscribe from topics
    - Query message history
    - Route messages based on patterns
    - Handle message priorities
    - Coordinate swarm behavior
    """
    
    def __init__(self, runtime_dir: Optional[Path] = None):
        """Initialize a new AgentBus instance.
        
        Args:
            runtime_dir: Optional runtime directory for message persistence
        """
        super().__init__()
        self._message_history: List[BusMessage] = []
        self._runtime_dir = runtime_dir
        
        if runtime_dir:
            self._history_file = runtime_dir / "message_history.json"
            self._load_history()
        
    def _load_history(self) -> None:
        """Load message history from file."""
        try:
            if self._history_file.exists():
                with open(self._history_file, 'r') as f:
                    data = json.load(f)
                    for msg_data in data:
                        message = BusMessage.from_dict(msg_data)
                        self._message_history.append(message)
        except Exception as e:
            logger.error(f"Error loading message history: {e}")
            
    def _save_history(self) -> None:
        """Save message history to file."""
        try:
            with open(self._history_file, 'w') as f:
                json.dump([msg.to_dict() for msg in self._message_history], f)
        except Exception as e:
            logger.error(f"Error saving message history: {e}")
        
    async def publish(self, topic: str, content: Any, sender: str, 
                     metadata: Optional[Dict[str, Any]] = None,
                     priority: MessagePriority = MessagePriority.NORMAL,
                     pattern: Optional[str] = None,
                     mode: MessageMode = MessageMode.NORMAL) -> str:
        """Publish a message to a topic.
        
        Args:
            topic: Topic to publish to
            content: Message content
            sender: Sender identifier
            metadata: Optional message metadata
            priority: Message priority
            pattern: Optional pattern for routing
            mode: Message mode
            
        Returns:
            str: Message ID
        """
        message = BusMessage(
            id=str(uuid4()),
            topic=topic,
            content=content,
            sender=sender,
            metadata=metadata or {},
            priority=priority,
            mode=mode,
            timestamp=datetime.now()
        )
        
        async with self._lock:
            self._message_history.append(message)
            self._message_queue.put((-priority.value, message))
            
            # Process subscribers
            await self._notify_subscribers(message)
            
            # Save history if runtime directory is configured
            if self._runtime_dir:
                self._save_history()
                            
        return message.id
    
    def subscribe(self, topic: str, callback: Callable, pattern: Optional[str] = None) -> None:
        """
        Subscribe to a topic with a callback function.
        
        Args:
            topic: The topic to subscribe to
            callback: An async callback function that takes a Message parameter
            pattern: Optional regex pattern for topic matching
        """
        if pattern:
            compiled_pattern = re.compile(pattern)
            if compiled_pattern not in self._pattern_subscribers:
                self._pattern_subscribers[compiled_pattern] = set()
            self._pattern_subscribers[compiled_pattern].add(callback)
        else:
            if topic not in self._subscribers:
                self._subscribers[topic] = set()
            self._subscribers[topic].add(callback)
        
    def unsubscribe(self, topic: str, callback: Callable, pattern: Optional[str] = None) -> None:
        """
        Unsubscribe a callback from a topic.
        
        Args:
            topic: The topic to unsubscribe from
            callback: The callback function to remove
            pattern: Optional pattern used for subscription
        """
        if pattern:
            compiled_pattern = re.compile(pattern)
            if compiled_pattern in self._pattern_subscribers:
                self._pattern_subscribers[compiled_pattern].discard(callback)
                if not self._pattern_subscribers[compiled_pattern]:
                    del self._pattern_subscribers[compiled_pattern]
        else:
            if topic in self._subscribers:
                self._subscribers[topic].discard(callback)
                if not self._subscribers[topic]:
                    del self._subscribers[topic]
                
    async def get_message_history(self, topic: Optional[str] = None, 
                                limit: int = 100,
                                priority: Optional[MessagePriority] = None,
                                mode: Optional[MessageMode] = None) -> List[BusMessage]:
        """
        Get message history with filtering options.
        
        Args:
            topic: Optional topic to filter messages by
            limit: Maximum number of messages to return
            priority: Optional priority level to filter by
            mode: Optional message mode to filter by
            
        Returns:
            List[BusMessage]: List of messages matching the criteria
        """
        async with self._lock:
            messages = self._message_history.copy()
            
            if topic:
                messages = [m for m in messages if m.topic == topic]
            if priority:
                messages = [m for m in messages if m.priority == priority]
            if mode:
                messages = [m for m in messages if m.mode == mode]
                
            return messages[-limit:]
            
    def get_subscriber_count(self, topic: str) -> int:
        """
        Get the number of subscribers for a topic.
        
        Args:
            topic: The topic to check
            
        Returns:
            int: Number of subscribers
        """
        count = len(self._subscribers.get(topic, set()))
        for pattern in self._pattern_subscribers:
            if pattern.match(topic):
                count += len(self._pattern_subscribers[pattern])
        return count
        
        
    async def _process_message(self, message: BusMessage) -> None:
        """Process a single message.
        
        Args:
            message: The message to process
        """
        try:
            # Convert BusMessage to Message for processing
            processed_message = Message(
                from_agent=message.sender,
                to_agent=message.topic,
                content=message.content,
                mode=message.mode,
                metadata=message.metadata
            )
            
            # Process message based on mode
            if message.mode == MessageMode.COMMAND:
                # Handle command processing
                pass
            elif message.mode == MessageMode.SYSTEM:
                # Handle system message processing
                pass
            else:
                # Handle normal message processing
                pass
                
        except Exception as e:
            logger.error(f"Error processing message {message.id}: {e}")
            
    def cleanup(self) -> None:
        """Clean up resources."""
        self._processing = False
        if self._runtime_dir:
            self._save_history() 