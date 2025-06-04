"""
Unified Message System
---------------------
Provides a single source of truth for all message handling in Dream.OS.
Consolidates functionality from:
- MessageSystem
- AgentBus
- CellPhone
- MessageProcessor
"""

import json
import logging
import asyncio
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Callable, Pattern
from datetime import datetime
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

from .common import Message, MessageMode, MessagePriority
from queue import PriorityQueue
import re
from uuid import uuid4

logger = logging.getLogger('dreamos.messaging')

class MessageQueue(ABC):
    """Abstract base class for message queue implementations."""
    
    @abstractmethod
    async def enqueue(self, message: Message) -> bool:
        """Add message to queue."""
        pass
    
    @abstractmethod
    async def get_messages(self, agent_id: str) -> List[Message]:
        """Get all pending messages for an agent."""
        pass
    
    @abstractmethod
    async def acknowledge(self, message_id: str) -> bool:
        """Mark message as processed."""
        pass

class MessageHistory(ABC):
    """Abstract base class for message history implementations."""
    
    @abstractmethod
    async def record(self, message: Message) -> bool:
        """Record a message in history."""
        pass
    
    @abstractmethod
    async def get_history(
        self,
        agent_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Message]:
        """Get message history with optional filtering."""
        pass

class MessageRouter(ABC):
    """Abstract base class for message routing implementations."""
    
    @abstractmethod
    async def route(self, message: Message) -> bool:
        """Route a message to its destination."""
        pass

class SimpleRouter(MessageRouter):
    """Simple message router implementation."""
    
    async def route(self, message: Message) -> bool:
        """Route a message to its destination."""
        return True  # Always succeed for now

class SimpleQueue(MessageQueue):
    """Simple message queue implementation."""
    
    def __init__(self):
        self._messages: Dict[str, List[Message]] = {}
    
    async def enqueue(self, message: Message) -> bool:
        """Add message to queue."""
        if message.to_agent not in self._messages:
            self._messages[message.to_agent] = []
        self._messages[message.to_agent].append(message)
        return True
    
    async def get_messages(self, agent_id: str) -> List[Message]:
        """Get all pending messages for an agent."""
        return self._messages.get(agent_id, [])
    
    async def acknowledge(self, message_id: str) -> bool:
        """Mark message as processed."""
        return True

class SimpleHistory(MessageHistory):
    """Simple message history implementation."""
    
    def __init__(self):
        self._history: List[Message] = []
    
    async def record(self, message: Message) -> bool:
        """Record a message in history."""
        self._history.append(message)
        return True
    
    async def get_history(
        self,
        agent_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Message]:
        """Get message history with optional filtering."""
        filtered = self._history
        if agent_id:
            filtered = [m for m in filtered if m.to_agent == agent_id]
        if start_time:
            filtered = [m for m in filtered if m.timestamp >= start_time]
        if end_time:
            filtered = [m for m in filtered if m.timestamp <= end_time]
        if limit:
            filtered = filtered[-limit:]
        return filtered

class UnifiedMessageSystem:
    """Unified message handling system for Dream.OS."""
    
    _instance = None
    _lock = threading.Lock()
    _async_lock = asyncio.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Ensure singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(
        self,
        runtime_dir: Optional[Path] = None,
        queue: Optional[MessageQueue] = None,
        history: Optional[MessageHistory] = None,
        router: Optional[MessageRouter] = None
    ):
        """Initialize message system.
        
        Args:
            runtime_dir: Base runtime directory
            queue: Message queue implementation
            history: Message history implementation
            router: Message router implementation
        """
        if hasattr(self, 'initialized'):
            return
            
        self.runtime_dir = runtime_dir
        self.queue = queue or SimpleQueue()
        self.history = history or SimpleHistory()
        self.router = router or SimpleRouter()
        
        # Message bus functionality
        self._subscribers: Dict[str, Set[Callable]] = {}
        self._pattern_subscribers: Dict[Pattern, Set[Callable]] = {}
        self._message_queue: PriorityQueue = PriorityQueue()
        self._processing = False
        
        # Initialize components
        self._setup_components()
        self.initialized = True
        
        logger.info("Unified message system initialized")
    
    def _setup_components(self):
        """Set up system components."""
        if self.runtime_dir:
            # Set up persistent storage
            self._history_file = self.runtime_dir / "data" / "message_history.json"
            self._history_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Load existing history
            self._load_history()
    
    async def send(
        self,
        to_agent: str,
        content: str,
        mode: MessageMode = MessageMode.NORMAL,
        priority: MessagePriority = MessagePriority.NORMAL,
        from_agent: str = "system",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send a message through the system.
        
        Args:
            to_agent: Target agent ID
            content: Message content
            mode: Message mode
            priority: Message priority
            from_agent: Sender agent ID
            metadata: Additional message metadata
            
        Returns:
            bool: True if message was successfully processed
        """
        try:
            # Create message
            message = Message(
                message_id=str(uuid4()),
                from_agent=from_agent,
                to_agent=to_agent,
                content=content,
                mode=mode,
                priority=priority,
                timestamp=datetime.now(),
                metadata=metadata or {}
            )
            
            # Route message
            if not await self.router.route(message):
                logger.error(f"Failed to route message to {to_agent}")
                return False
            
            # Add to queue
            if not await self.queue.enqueue(message):
                logger.error(f"Failed to queue message for {to_agent}")
                return False
            
            # Record in history
            if not await self.history.record(message):
                logger.error(f"Failed to record message in history")
                return False
            
            # Notify subscribers
            await self._notify_subscribers(message)
            
            logger.info(f"Message sent successfully to {to_agent}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    async def receive(self, agent_id: str) -> List[Message]:
        """Get pending messages for an agent.
        
        Args:
            agent_id: ID of agent to get messages for
            
        Returns:
            List[Message]: List of pending messages
        """
        try:
            messages = await self.queue.get_messages(agent_id)
            logger.info(f"Retrieved {len(messages)} messages for {agent_id}")
            return messages
        except Exception as e:
            logger.error(f"Error receiving messages for {agent_id}: {e}")
            return []
    
    async def subscribe(self, topic: str, handler: Callable) -> None:
        """Subscribe to a topic.
        
        Args:
            topic: Topic to subscribe to
            handler: Callback function to handle messages
        """
        if topic not in self._subscribers:
            self._subscribers[topic] = set()
        self._subscribers[topic].add(handler)
    
    async def subscribe_pattern(self, pattern: str, handler: Callable) -> None:
        """Subscribe to messages matching a pattern.
        
        Args:
            pattern: Regex pattern to match
            handler: Callback function to handle messages
        """
        compiled_pattern = re.compile(pattern)
        self._pattern_subscribers[compiled_pattern] = set()
        self._pattern_subscribers[compiled_pattern].add(handler)
    
    async def unsubscribe(self, topic: str, handler: Callable) -> None:
        """Unsubscribe from a topic.
        
        Args:
            topic: Topic to unsubscribe from
            handler: Handler to remove
        """
        if topic in self._subscribers:
            self._subscribers[topic].discard(handler)
    
    async def unsubscribe_pattern(self, pattern: str, handler: Callable) -> None:
        """Unsubscribe from a pattern.
        
        Args:
            pattern: Pattern to unsubscribe from
            handler: Handler to remove
        """
        compiled_pattern = re.compile(pattern)
        if compiled_pattern in self._pattern_subscribers:
            self._pattern_subscribers[compiled_pattern].discard(handler)
    
    async def get_history(
        self,
        agent_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Message]:
        """Get message history with optional filtering.
        
        Args:
            agent_id: Optional agent ID to filter by
            start_time: Optional start time to filter by
            end_time: Optional end time to filter by
            limit: Optional maximum number of messages to return
            
        Returns:
            List[Message]: List of historical messages
        """
        try:
            return await self.history.get_history(
                agent_id=agent_id,
                start_time=start_time,
                end_time=end_time,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error getting message history: {e}")
            return []
    
    async def _notify_subscribers(self, message: Message) -> None:
        """Notify subscribers of a new message.
        
        Args:
            message: Message to notify about
        """
        # Notify direct subscribers
        if message.to_agent in self._subscribers:
            for handler in self._subscribers[message.to_agent]:
                try:
                    await handler(message)
                except Exception as e:
                    logger.error(f"Error in subscriber handler: {e}")
        
        # Notify pattern subscribers
        for pattern, handlers in self._pattern_subscribers.items():
            if pattern.match(message.to_agent):
                for handler in handlers:
                    try:
                        await handler(message)
                    except Exception as e:
                        logger.error(f"Error in pattern subscriber handler: {e}")
    
    def _load_history(self) -> None:
        """Load message history from file."""
        try:
            if self._history_file.exists():
                with open(self._history_file, 'r') as f:
                    data = json.load(f)
                    for msg_data in data:
                        message = Message.from_dict(msg_data)
                        self.history.record(message)
        except Exception as e:
            logger.error(f"Error loading message history: {e}")
    
    def _save_history(self) -> None:
        """Save message history to file."""
        try:
            history = self.history.get_history()
            with open(self._history_file, 'w') as f:
                json.dump([msg.to_dict() for msg in history], f)
        except Exception as e:
            logger.error(f"Error saving message history: {e}")
    
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
        if self.runtime_dir:
            self._save_history()
    
    async def _process_message(self, message: Message) -> None:
        """Process a single message.
        
        Args:
            message: Message to process
        """
        try:
            # Process based on mode
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
            logger.error(f"Error processing message {message.message_id}: {e}")
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        self._processing = False
        if self.runtime_dir:
            self._save_history() 