"""
Message Queue Implementation
--------------------------
Provides persistent message queue functionality for the unified message system.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from queue import PriorityQueue
from .common import Message, MessagePriority
from .unified_message_system import MessageQueue

logger = logging.getLogger('dreamos.messaging.queue')

class PersistentMessageQueue(MessageQueue):
    """Persistent message queue implementation."""
    
    def __init__(self, queue_dir: Path):
        """Initialize queue.
        
        Args:
            queue_dir: Directory for queue storage
        """
        self.queue_dir = queue_dir
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory queues by agent
        self._queues: Dict[str, PriorityQueue] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        
        # Load existing queues
        self._load_queues()
    
    def _load_queues(self) -> None:
        """Load existing queues from disk."""
        try:
            for queue_file in self.queue_dir.glob("*.json"):
                agent_id = queue_file.stem
                self._queues[agent_id] = PriorityQueue()
                self._locks[agent_id] = asyncio.Lock()
                
                with open(queue_file, 'r') as f:
                    messages = json.load(f)
                    for msg_data in messages:
                        message = Message.from_dict(msg_data)
                        self._queues[agent_id].put(
                            (-message.priority.value, message)
                        )
                        
            logger.info(f"Loaded {len(self._queues)} message queues")
        except Exception as e:
            logger.error(f"Error loading message queues: {e}")
    
    def _save_queue(self, agent_id: str) -> None:
        """Save queue to disk.
        
        Args:
            agent_id: ID of agent whose queue to save
        """
        try:
            queue_file = self.queue_dir / f"{agent_id}.json"
            messages = []
            
            # Get all messages from queue
            temp_queue = PriorityQueue()
            while not self._queues[agent_id].empty():
                _, message = self._queues[agent_id].get()
                messages.append(message.to_dict())
                temp_queue.put((-message.priority.value, message))
            
            # Restore queue
            self._queues[agent_id] = temp_queue
            
            # Save to disk
            with open(queue_file, 'w') as f:
                json.dump(messages, f)
                
        except Exception as e:
            logger.error(f"Error saving queue for {agent_id}: {e}")
    
    async def enqueue(self, message: Message) -> bool:
        """Add message to queue.
        
        Args:
            message: Message to enqueue
            
        Returns:
            bool: True if message was successfully queued
        """
        try:
            agent_id = message.to_agent
            
            # Create queue if needed
            if agent_id not in self._queues:
                self._queues[agent_id] = PriorityQueue()
                self._locks[agent_id] = asyncio.Lock()
            
            # Add to queue
            async with self._locks[agent_id]:
                self._queues[agent_id].put(
                    (-message.priority.value, message)
                )
                self._save_queue(agent_id)
            
            logger.info(f"Message queued for {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error enqueueing message: {e}")
            return False
    
    async def get_messages(self, agent_id: str) -> List[Message]:
        """Get all pending messages for an agent.
        
        Args:
            agent_id: ID of agent to get messages for
            
        Returns:
            List[Message]: List of pending messages
        """
        try:
            if agent_id not in self._queues:
                return []
            
            messages = []
            async with self._locks[agent_id]:
                while not self._queues[agent_id].empty():
                    _, message = self._queues[agent_id].get()
                    messages.append(message)
                
                # Save empty queue
                self._save_queue(agent_id)
            
            logger.info(f"Retrieved {len(messages)} messages for {agent_id}")
            return messages
            
        except Exception as e:
            logger.error(f"Error getting messages for {agent_id}: {e}")
            return []
    
    async def acknowledge(self, message_id: str) -> bool:
        """Mark message as processed.
        
        Args:
            message_id: ID of message to acknowledge
            
        Returns:
            bool: True if message was successfully acknowledged
        """
        try:
            # Find message in queues
            for agent_id, queue in self._queues.items():
                async with self._locks[agent_id]:
                    temp_queue = PriorityQueue()
                    found = False
                    
                    while not queue.empty():
                        _, message = queue.get()
                        if message.message_id == message_id:
                            message.status = "processed"
                            found = True
                        temp_queue.put((-message.priority.value, message))
                    
                    # Restore queue
                    self._queues[agent_id] = temp_queue
                    
                    if found:
                        self._save_queue(agent_id)
                        logger.info(f"Message {message_id} acknowledged")
                        return True
            
            logger.warning(f"Message {message_id} not found")
            return False
            
        except Exception as e:
            logger.error(f"Error acknowledging message {message_id}: {e}")
            return False 
