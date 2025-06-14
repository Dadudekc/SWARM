"""
Unified Message System
---------------------
Provides a single source of truth for all message handling in Dream.OS.
Consolidates functionality from and supersedes:
- MessageSystem
- AgentBus
- CellPhone
- MessageProcessor
"""

from __future__ import annotations

import json
import logging
import asyncio
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Callable, Pattern, TypeVar, Generic
from datetime import datetime
from dataclasses import dataclass
from abc import ABC, abstractmethod
from queue import PriorityQueue
import re
from uuid import uuid4

from dreamos.core.messaging.base import BaseMessagingComponent
from dreamos.core.messaging.enums import MessageMode, MessagePriority
from dreamos.core.messaging.common import Message
from ..utils.metrics import metrics, logger, log_operation
from ..utils.exceptions import handle_error
from ..utils.file_ops import FileManager

logger = logging.getLogger('dreamos.messaging')

T = TypeVar('T')

@dataclass
class Message(Generic[T]):
    """Message data class."""
    message_id: str
    type: str
    content: T
    from_agent: str
    to_agent: str
    priority: int = 0
    timestamp: datetime = datetime.now()
    metadata: Optional[Dict[str, Any]] = None

class MessageQueue(ABC, Generic[T]):
    """Abstract base class for message queue implementations."""
    
    def __init__(self, name: str):
        """Initialize message queue.
        
        Args:
            name: Name of the queue
        """
        self.name = name
        self._metrics = {
            'enqueue': metrics.counter(
                'message_queue_enqueue_total',
                'Total messages enqueued',
                ['queue', 'type']
            ),
            'dequeue': metrics.counter(
                'message_queue_dequeue_total',
                'Total messages dequeued',
                ['queue', 'type']
            ),
            'ack': metrics.counter(
                'message_queue_ack_total',
                'Total messages acknowledged',
                ['queue', 'type']
            ),
            'error': metrics.counter(
                'message_queue_error_total',
                'Total queue errors',
                ['queue', 'operation']
            ),
            'duration': metrics.histogram(
                'message_queue_duration_seconds',
                'Queue operation duration',
                ['queue', 'operation']
            )
        }
    
    @abstractmethod
    async def enqueue(self, message: Message[T]) -> bool:
        """Add message to queue."""
        pass
    
    @abstractmethod
    async def dequeue(self, agent_id: str) -> Optional[Message[T]]:
        """Get next message for agent."""
        pass
    
    @abstractmethod
    async def acknowledge(self, message_id: str) -> bool:
        """Mark message as processed."""
        pass

class PersistentMessageQueue(MessageQueue[T]):
    """Message queue with persistent storage."""
    
    def __init__(
        self,
        name: str,
        storage_dir: Path,
        max_size: int = 1000
    ):
        """Initialize persistent queue.
        
        Args:
            name: Queue name
            storage_dir: Directory for message storage
            max_size: Maximum queue size
        """
        super().__init__(name)
        self.storage_dir = Path(storage_dir)
        self.max_size = max_size
        self._queue: PriorityQueue[Message[T]] = PriorityQueue(maxsize=max_size)
        self._lock = threading.Lock()
        self._file_manager = FileManager(
            self.storage_dir / "queue.json",
            max_retries=3,
            backup_enabled=True
        )
        
        # Load existing messages
        self._load_messages()
    
    def _load_messages(self):
        """Load messages from storage."""
        try:
            data = self._file_manager.read()
            if data:
                for msg_data in data:
                    message = Message[T](
                        message_id=msg_data['message_id'],
                        type=msg_data['type'],
                        content=msg_data['content'],
                        from_agent=msg_data['from_agent'],
                        to_agent=msg_data['to_agent'],
                        priority=msg_data.get('priority', 0),
                        timestamp=datetime.fromisoformat(msg_data['timestamp']),
                        metadata=msg_data.get('metadata')
                    )
                    self._queue.put((message.priority, message))
        except Exception as e:
            error = handle_error(e, {
                "queue": self.name,
                "operation": "load_messages"
            })
            logger.error(f"Failed to load messages: {str(error)}")
            self._metrics['error'].labels(
                queue=self.name,
                operation="load_messages"
            ).inc()
    
    def _save_messages(self):
        """Save messages to storage."""
        try:
            messages = []
            with self._lock:
                while not self._queue.empty():
                    _, message = self._queue.get()
                    messages.append({
                        'message_id': message.message_id,
                        'type': message.type,
                        'content': message.content,
                        'from_agent': message.from_agent,
                        'to_agent': message.to_agent,
                        'priority': message.priority,
                        'timestamp': message.timestamp.isoformat(),
                        'metadata': message.metadata
                    })
            
            self._file_manager.write(messages)
            
        except Exception as e:
            error = handle_error(e, {
                "queue": self.name,
                "operation": "save_messages"
            })
            logger.error(f"Failed to save messages: {str(error)}")
            self._metrics['error'].labels(
                queue=self.name,
                operation="save_messages"
            ).inc()
    
    @log_operation('message_enqueue', metrics='enqueue', duration='duration')
    async def enqueue(self, message: Message[T]) -> bool:
        """Add message to queue."""
        try:
            with self._lock:
                if self._queue.full():
                    logger.warning(f"Queue {self.name} is full")
                    return False
                
                self._queue.put((message.priority, message))
                self._save_messages()
                
                self._metrics['enqueue'].labels(
                    queue=self.name,
                    type=message.type
                ).inc()
                
                return True
                
        except Exception as e:
            error = handle_error(e, {
                "queue": self.name,
                "operation": "enqueue",
                "message": message.message_id
            })
            logger.error(f"Failed to enqueue message: {str(error)}")
            self._metrics['error'].labels(
                queue=self.name,
                operation="enqueue"
            ).inc()
            return False
    
    @log_operation('message_dequeue', metrics='dequeue', duration='duration')
    async def dequeue(self, agent_id: str) -> Optional[Message[T]]:
        """Get next message for agent."""
        try:
            with self._lock:
                # Find next message for agent
                messages = []
                found = None
                
                while not self._queue.empty():
                    _, message = self._queue.get()
                    if message.to_agent == agent_id:
                        found = message
                        break
                    messages.append((message.priority, message))
                
                # Put other messages back
                for priority, message in messages:
                    self._queue.put((priority, message))
                
                if found:
                    self._metrics['dequeue'].labels(
                        queue=self.name,
                        type=found.type
                    ).inc()
                
                return found
                
        except Exception as e:
            error = handle_error(e, {
                "queue": self.name,
                "operation": "dequeue",
                "agent": agent_id
            })
            logger.error(f"Failed to dequeue message: {str(error)}")
            self._metrics['error'].labels(
                queue=self.name,
                operation="dequeue"
            ).inc()
            return None
    
    @log_operation('message_ack', metrics='ack', duration='duration')
    async def acknowledge(self, message_id: str) -> bool:
        """Mark message as processed."""
        try:
            with self._lock:
                # Find and remove message
                messages = []
                found = False
                
                while not self._queue.empty():
                    _, message = self._queue.get()
                    if message.message_id == message_id:
                        found = True
                        self._metrics['ack'].labels(
                            queue=self.name,
                            type=message.type
                        ).inc()
                        break
                    messages.append((message.priority, message))
                
                # Put other messages back
                for priority, message in messages:
                    self._queue.put((priority, message))
                
                if found:
                    self._save_messages()
                
                return found
                
        except Exception as e:
            error = handle_error(e, {
                "queue": self.name,
                "operation": "acknowledge",
                "message": message_id
            })
            logger.error(f"Failed to acknowledge message: {str(error)}")
            self._metrics['error'].labels(
                queue=self.name,
                operation="acknowledge"
            ).inc()
            return False

class MessageProcessor(Generic[T]):
    """Processes messages from a queue."""
    
    def __init__(
        self,
        queue: MessageQueue[T],
        handlers: Dict[str, Callable[[Message[T]], Awaitable[bool]]]
    ):
        """Initialize message processor.
        
        Args:
            queue: Message queue to process
            handlers: Message type to handler mapping
        """
        self.queue = queue
        self.handlers = handlers
        self._metrics = {
            'process': metrics.counter(
                'message_processor_total',
                'Total messages processed',
                ['type', 'result']
            ),
            'error': metrics.counter(
                'message_processor_error_total',
                'Total processing errors',
                ['type']
            ),
            'duration': metrics.histogram(
                'message_processor_duration_seconds',
                'Processing duration',
                ['type']
            )
        }
    
    @log_operation('message_process', metrics='process', duration='duration')
    async def process_message(self, message: Message[T]) -> bool:
        """Process a single message.
        
        Args:
            message: Message to process
            
        Returns:
            True if processing was successful
        """
        try:
            # Get handler for message type
            handler = self.handlers.get(message.type)
            if not handler:
                logger.warning(f"No handler for message type: {message.type}")
                self._metrics['process'].labels(
                    type=message.type,
                    result="no_handler"
                ).inc()
                return False
            
            # Process message
            success = await handler(message)
            
            # Record metrics
            self._metrics['process'].labels(
                type=message.type,
                result="success" if success else "failure"
            ).inc()
            
            return success
            
        except Exception as e:
            error = handle_error(e, {
                "message": message.message_id,
                "type": message.type,
                "operation": "process"
            })
            logger.error(f"Error processing message: {str(error)}")
            self._metrics['error'].labels(
                type=message.type
            ).inc()
            return False
    
    async def process_queue(self, agent_id: str):
        """Process messages from queue for an agent.
        
        Args:
            agent_id: ID of agent to process messages for
        """
        while True:
            try:
                # Get next message
                message = await self.queue.dequeue(agent_id)
                if not message:
                    await asyncio.sleep(0.1)
                    continue
                
                # Process message
                success = await self.process_message(message)
                
                # Acknowledge if successful
                if success:
                    await self.queue.acknowledge(message.message_id)
                
            except Exception as e:
                error = handle_error(e, {
                    "agent": agent_id,
                    "operation": "process_queue"
                })
                logger.error(f"Error processing queue: {str(error)}")
                await asyncio.sleep(1)  # Prevent tight loop on error

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
    
    async def dequeue(self, agent_id: str):
        """Pop first message for the agent if present."""
        msgs = self._messages.get(agent_id)
        if msgs:
            return msgs.pop(0)
        return None

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

class MessageSystem(BaseMessagingComponent):
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
            
        super().__init__()
        self.runtime_dir = runtime_dir
        self.queue = queue or SimpleQueue()
        self.history = history or SimpleHistory()
        self.router = router or SimpleRouter()
        
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
            to_agent: Recipient agent ID
            content: Message content
            mode: Message mode
            priority: Message priority
            from_agent: Sender agent ID
            metadata: Optional message metadata
            
        Returns:
            bool: True if message was sent successfully
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
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        self._processing = False
        if self.runtime_dir:
            self._save_history()

# Backwards compatibility alias
UnifiedMessageSystem = MessageSystem
