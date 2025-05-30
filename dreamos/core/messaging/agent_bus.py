"""
AgentBus - A message bus implementation for agent communication.

This module provides a centralized message bus for agent communication,
allowing agents to publish and subscribe to messages in a decoupled manner.
Supports swarm-like behavior through advanced routing and pattern matching.
"""

from typing import Any, Callable, Dict, List, Optional, Set, Pattern
from dataclasses import dataclass
from datetime import datetime
import asyncio
import logging
import re
from uuid import uuid4
from enum import Enum
from queue import PriorityQueue
from pathlib import Path
import json

from .message import Message, MessageMode

logger = logging.getLogger(__name__)

class MessagePriority(Enum):
    """Message priority levels for swarm coordination."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

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

class AgentBus:
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
        self._subscribers: Dict[str, Set[Callable]] = {}
        self._pattern_subscribers: Dict[Pattern, Set[Callable]] = {}
        self._message_history: List[BusMessage] = []
        self._message_queue: PriorityQueue = PriorityQueue()
        self._lock = asyncio.Lock()
        self._processing = False
        self._runtime_dir = runtime_dir
        
        if runtime_dir:
            self._history_file = runtime_dir / "message_history.json"
            self._load_history()
        
    def _load_history(self) -> None:
        """Load message history from disk."""
        try:
            if self._history_file.exists():
                with open(self._history_file) as f:
                    history_data = json.load(f)
                    self._message_history = [
                        BusMessage(
                            id=msg["id"],
                            topic=msg["topic"],
                            content=msg["content"],
                            sender=msg["sender"],
                            timestamp=datetime.fromisoformat(msg["timestamp"]),
                            metadata=msg["metadata"],
                            priority=MessagePriority[msg["priority"]],
                            pattern=msg.get("pattern"),
                            mode=MessageMode[msg.get("mode", "NORMAL")]
                        )
                        for msg in history_data
                    ]
        except Exception as e:
            logger.error(f"Error loading message history: {e}")
            
    def _save_history(self) -> None:
        """Save message history to disk."""
        if not self._runtime_dir:
            return
            
        try:
            history_data = [
                {
                    "id": msg.id,
                    "topic": msg.topic,
                    "content": msg.content,
                    "sender": msg.sender,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata,
                    "priority": msg.priority.name,
                    "pattern": msg.pattern,
                    "mode": msg.mode.name
                }
                for msg in self._message_history
            ]
            
            with open(self._history_file, 'w') as f:
                json.dump(history_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving message history: {e}")
        
    async def publish(self, topic: str, content: Any, sender: str, 
                     metadata: Optional[Dict[str, Any]] = None,
                     priority: MessagePriority = MessagePriority.NORMAL,
                     pattern: Optional[str] = None,
                     mode: MessageMode = MessageMode.NORMAL) -> str:
        """
        Publish a message to a specific topic with priority and pattern support.
        
        Args:
            topic: The topic to publish to
            content: The message content
            sender: The ID of the agent sending the message
            metadata: Optional metadata to attach to the message
            priority: Message priority level
            pattern: Optional pattern for routing
            mode: Message mode for processing
            
        Returns:
            str: The ID of the published message
        """
        message = BusMessage(
            id=str(uuid4()),
            topic=topic,
            content=content,
            sender=sender,
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
            priority=priority,
            pattern=pattern,
            mode=mode
        )
        
        async with self._lock:
            self._message_history.append(message)
            self._message_queue.put((-priority.value, message))
            
            # Process subscribers
            if topic in self._subscribers:
                for callback in self._subscribers[topic]:
                    try:
                        await callback(message)
                    except Exception as e:
                        logger.error(f"Error in subscriber callback for topic {topic}: {e}")
            
            # Process pattern subscribers
            for pattern, callbacks in self._pattern_subscribers.items():
                if pattern.match(topic):
                    for callback in callbacks:
                        try:
                            await callback(message)
                        except Exception as e:
                            logger.error(f"Error in pattern subscriber callback for topic {topic}: {e}")
            
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
        
    async def start_processing(self):
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
                
    async def stop_processing(self):
        """Stop processing the message queue."""
        self._processing = False
        
    async def _process_message(self, message: BusMessage):
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
            
    def cleanup(self):
        """Clean up resources."""
        self._processing = False
        if self._runtime_dir:
            self._save_history() 