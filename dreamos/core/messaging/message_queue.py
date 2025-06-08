"""
Message Queue
-----------
Thread-safe message queue with proper locking and error handling.
"""

import json
import logging
import threading
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict

logger = logging.getLogger(__name__)

class MessageQueue:
    """Thread-safe message queue with priority support."""
    
    def __init__(self):
        """Initialize the message queue."""
        self._queues = defaultdict(list)  # agent_id -> list of messages
        self._locks = defaultdict(threading.Lock)  # agent_id -> lock
        self._subscribers = defaultdict(list)  # agent_id -> list of callbacks
        self._subscriber_lock = threading.Lock()
        
    def _get_queue(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get message queue for agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Message queue
        """
        return self._queues[agent_id]
        
    def _get_lock(self, agent_id: str) -> threading.Lock:
        """Get lock for agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Thread lock
        """
        return self._locks[agent_id]
        
    def enqueue(self, agent_id: str, message: Dict[str, Any]) -> bool:
        """Add message to queue.
        
        Args:
            agent_id: Agent identifier
            message: Message to enqueue
            
        Returns:
            True if successful
        """
        try:
            # Validate message
            if not isinstance(message, dict):
                logger.error(f"Invalid message format: {message}")
                return False
                
            # Add metadata
            message["timestamp"] = datetime.utcnow().isoformat()
            message["agent_id"] = agent_id
            
            # Enqueue with priority
            with self._get_lock(agent_id):
                queue = self._get_queue(agent_id)
                priority = message.get("priority", "NORMAL")
                
                # Insert based on priority
                if priority == "HIGH":
                    queue.insert(0, message)
                else:
                    queue.append(message)
                    
            # Notify subscribers
            self._notify_subscribers(agent_id, message)
            return True
            
        except Exception as e:
            logger.error(f"Failed to enqueue message: {e}")
            return False
            
    def dequeue(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get next message from queue.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Next message or None if empty
        """
        try:
            with self._get_lock(agent_id):
                queue = self._get_queue(agent_id)
                if not queue:
                    return None
                return queue.pop(0)
                
        except Exception as e:
            logger.error(f"Failed to dequeue message: {e}")
            return None
            
    def peek(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Peek at next message without removing it.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Next message or None if empty
        """
        try:
            with self._get_lock(agent_id):
                queue = self._get_queue(agent_id)
                return queue[0] if queue else None
                
        except Exception as e:
            logger.error(f"Failed to peek message: {e}")
            return None
            
    def clear(self, agent_id: str) -> bool:
        """Clear message queue for agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            True if successful
        """
        try:
            with self._get_lock(agent_id):
                self._get_queue(agent_id).clear()
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear queue: {e}")
            return False
            
    def subscribe(self, agent_id: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Subscribe to messages for agent.
        
        Args:
            agent_id: Agent identifier
            callback: Callback function
        """
        with self._subscriber_lock:
            self._subscribers[agent_id].append(callback)
            
    def unsubscribe(self, agent_id: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Unsubscribe from messages for agent.
        
        Args:
            agent_id: Agent identifier
            callback: Callback function to remove
        """
        with self._subscriber_lock:
            if agent_id in self._subscribers:
                self._subscribers[agent_id].remove(callback)
                
    def _notify_subscribers(self, agent_id: str, message: Dict[str, Any]) -> None:
        """Notify subscribers of new message.
        
        Args:
            agent_id: Agent identifier
            message: Message to notify about
        """
        with self._subscriber_lock:
            for callback in self._subscribers[agent_id]:
                try:
                    callback(message)
                except Exception as e:
                    logger.error(f"Subscriber callback failed: {e}")
                    
    def get_queue_size(self, agent_id: str) -> int:
        """Get number of messages in queue.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Queue size
        """
        try:
            with self._get_lock(agent_id):
                return len(self._get_queue(agent_id))
                
        except Exception as e:
            logger.error(f"Failed to get queue size: {e}")
            return 0
            
    def get_all_messages(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all messages in queue.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            List of messages
        """
        try:
            with self._get_lock(agent_id):
                return self._get_queue(agent_id).copy()
                
        except Exception as e:
            logger.error(f"Failed to get messages: {e}")
            return [] 
