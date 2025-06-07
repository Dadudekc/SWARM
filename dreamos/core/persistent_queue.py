"""
Persistent Queue

A file-based persistent queue implementation with file locking to prevent race conditions.
"""

import time
import logging
import os
import json
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from datetime import datetime
from filelock import FileLock, Timeout

from dreamos.core.messaging.common import Message, MessagePriority
from dreamos.core.message import Message as LegacyMessage
from .utils.file_utils import (
    ensure_dir,
    safe_write,
    safe_read,
)
from .utils.json_utils import (
    load_json,
    save_json,
)
from social.utils.log_manager import LogManager

logger = logging.getLogger('persistent_queue')

class PersistentQueue:
    """A file-based persistent queue with file locking."""
    
    def __init__(self, queue_file: str = "runtime/queue/messages.json"):
        """Initialize the persistent queue.
        
        Args:
            queue_file: Path to the JSON file used for the queue
        """
        self.queue_file = Path(queue_file)
        self.queue_path = str(self.queue_file)  # Store path as string for compatibility
        self.lock_file = self.queue_file.with_suffix('.lock')
        self.file_lock = FileLock(str(self.lock_file))
        self.max_size = 1000  # Maximum number of messages in queue
        self.max_history = 1000  # Maximum number of messages in history
        self.message_history = []  # Track message history
        self.last_enqueue_time = 0  # Track last enqueue time for rate limiting
        self.min_enqueue_interval = 0.1  # Minimum time between enqueues (100ms)
        self.rate_limit_window = 5.0  # 5 second window for rate limiting
        self.max_messages_per_window = 20  # Maximum 20 messages per 5-second window
        self.message_counts = {}  # Track message counts per window
        self._is_test_mode = False  # Flag to disable rate limiting in tests
        
        # Create queue directory if it doesn't exist
        ensure_dir(str(self.queue_file.parent))
        
        # Initialize queue file if it doesn't exist
        if not self.queue_file.exists():
            self._write_queue([])
    
    def _acquire_lock(self, timeout: int = 5) -> bool:
        """Acquire a lock file to prevent race conditions.
        
        Args:
            timeout: Maximum time to wait for lock in seconds
            
        Returns:
            bool: True if lock was acquired, False if timeout
        """
        try:
            self.file_lock.acquire(timeout=timeout)
            return True
        except Timeout:
            logger.error("Lock acquisition timed out")
            return False
        except Exception as e:
            logger.error(f"Error acquiring lock: {e}")
            return False
    
    def _release_lock(self):
        """Release the lock file."""
        try:
            if self.file_lock.is_locked:
                self.file_lock.release()
        except Exception as e:
            logger.error(f"Error releasing lock: {e}")
    
    def _read_queue(self) -> List[Dict]:
        """Read the current queue from file."""
        try:
            return load_json(self.queue_path, default=[])
        except FileOpsError as e:
            logger.error(f"Error reading queue: {e}")
            return []
    
    def _write_queue(self, queue: List[Dict]):
        """Write the queue to file."""
        try:
            save_json(self.queue_path, queue)
        except FileOpsError as e:
            logger.error(f"Error writing queue: {e}")
    
    def _check_rate_limit(self, agent_id: str) -> bool:
        """Check if rate limit is exceeded for an agent.
        
        Args:
            agent_id: ID of the agent to check
            
        Returns:
            bool: True if rate limit is not exceeded, False otherwise
        """
        if self._is_test_mode:
            return True
            
        current_time = time.time()
        
        # Clean up old message counts
        self.message_counts = {
            agent: counts for agent, counts in self.message_counts.items()
            if current_time - counts['window_start'] < self.rate_limit_window
        }
        
        # Initialize or update agent's message count
        if agent_id not in self.message_counts:
            self.message_counts[agent_id] = {
                'count': 1,
                'window_start': current_time
            }
            return True
            
        agent_counts = self.message_counts[agent_id]
        
        # Reset window if it's expired
        if current_time - agent_counts['window_start'] >= self.rate_limit_window:
            agent_counts['count'] = 1
            agent_counts['window_start'] = current_time
            return True
            
        # Check if rate limit is exceeded
        if agent_counts['count'] >= self.max_messages_per_window:
            return False
            
        agent_counts['count'] += 1
        return True
    
    def get_queue_size(self) -> int:
        """Get current queue size.
        
        Returns:
            int: Number of messages in queue
        """
        if not self._acquire_lock():
            logger.error("Failed to acquire lock for size check")
            return 0
            
        try:
            queue = self._read_queue()
            return len(queue)
        except Exception as e:
            logger.error(f"Error getting queue size: {e}")
            return 0
        finally:
            self._release_lock()
    
    def get_message(self) -> Optional[Message]:
        """Remove and return the next message from the queue as a Message object."""
        if not self._acquire_lock():
            return None
        try:
            queue = self._read_queue()
            if not queue:
                return None
            message_dict = queue.pop(0)
            self._write_queue(queue)
            return Message.from_dict(message_dict)
        except Exception as e:
            logger.error(f"Error dequeuing message: {e}")
            return None
        finally:
            self._release_lock()
    
    def clear_queue(self):
        """Clear all messages from the queue and message history."""
        if not self._acquire_lock():
            return
        try:
            self._write_queue([])
            self.message_history.clear()
            self.last_enqueue_time = 0  # Reset rate limiting
            self.message_counts.clear()  # Reset rate limiting counters
            logger.info("Queue cleared")
        finally:
            self._release_lock()
    
    def enqueue(self, message: Union[Dict, Message, LegacyMessage]) -> bool:
        """Add a message to the queue, inserting by priority (lower number = higher priority)."""
        if not isinstance(message, (dict, Message, LegacyMessage)):
            # Raise ValueError for invalid message types (fixes test_invalid_message)
            raise ValueError("Message must be a dict or Message object")
        if not self._acquire_lock():
            return False
        try:
            # Convert dict or legacy Message to new Message object
            if isinstance(message, dict):
                message = Message.from_dict(message)
            elif isinstance(message, LegacyMessage):
                message = Message.from_dict(message.to_dict())
            # Check queue size limit
            queue = self._read_queue()
            if len(queue) >= self.max_size:
                logger.warning(f"Queue size limit ({self.max_size}) reached")
                return False
            # Disable rate limiting in test mode (fixes test_queue_size_limit)
            if not self._is_test_mode:
                if not self._check_rate_limit(message.from_agent):
                    logger.warning(f"Rate limit exceeded for agent {message.from_agent}")
                    return False
            # Add message with priority
            message_dict = message.to_dict()
            # Preserve the priority name for deserialisation while storing a
            # numeric value for sorting purposes.
            priority_enum = getattr(message, 'priority', MessagePriority.NORMAL)
            priority_value = (
                priority_enum.value if isinstance(priority_enum, MessagePriority)
                else int(priority_enum)
            )
            message_dict['priority_value'] = priority_value
            # Insert message in priority order
            inserted = False
            for i, existing in enumerate(queue):
                if message_dict['priority_value'] < existing.get('priority_value', 0):
                    queue.insert(i, message_dict)
                    inserted = True
                    break
            if not inserted:
                queue.append(message_dict)
            self._write_queue(queue)
            # Update history
            self.message_history.append({
                'message': message_dict,
                'timestamp': time.time(),
                'status': 'queued'
            })
            # Trim history if needed
            if len(self.message_history) > self.max_history:
                self.message_history = self.message_history[-self.max_history:]
            logger.info(f"Message queued: {message.to_agent}")
            return True
        except Exception as e:
            logger.error(f"Error enqueueing message: {e}")
            return False
        finally:
            self._release_lock()
    
    def put(self, message: Dict) -> bool:
        """Alias for enqueue method.
        
        Args:
            message: Message to add (should be JSON serializable)
            
        Returns:
            bool: True if message was queued successfully
        """
        return self.enqueue(message)
    
    def get(self) -> Optional[Message]:
        """Alias for get_message method."""
        return self.get_message()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current queue status.
        
        Returns:
            Dict containing queue statistics
        """
        if not self._acquire_lock():
            return {"queue_size": 0, "messages": [], "history_size": 0}
            
        try:
            queue = self._read_queue()
            return {
                "queue_size": len(queue),
                "messages": queue,
                "history_size": len(self.message_history)
            }
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return {"queue_size": 0, "messages": [], "history_size": 0}
        finally:
            self._release_lock()
    
    def add_message(self, message: Union[Dict, Message, LegacyMessage]) -> bool:
        """Alias for enqueue method."""
        return self.enqueue(message)
    
    def clear_agent(self, agent_id: str) -> None:
        """Clear all messages for a specific agent.
        
        Args:
            agent_id: ID of the agent to clear messages for
        """
        if not self._acquire_lock():
            return
            
        try:
            queue = self._read_queue()
            queue = [msg for msg in queue if msg.get('to_agent') != agent_id]
            self._write_queue(queue)

            # Also clear from message history
            self.message_history = [
                msg for msg in self.message_history
                if msg.get('message', {}).get('to_agent') != agent_id
            ]
            
            # Clear rate limiting counters for this agent
            if agent_id in self.message_counts:
                del self.message_counts[agent_id]
                
            logger.info(f"Cleared messages for agent {agent_id}")
        finally:
            self._release_lock()
    
    def shutdown(self):
        """Clean up resources."""
        if not self._acquire_lock():
            return
            
        try:
            self._write_queue([])
            self.message_history.clear()
            self.message_counts.clear()
            self.last_enqueue_time = 0
            logger.info("Queue shutdown complete")
        finally:
            self._release_lock()
    
    def get_message_history(self, agent_id=None):
        """Get message history for an agent or all agents.
        
        Args:
            agent_id: Optional agent ID to filter history
            
        Returns:
            List of Message objects
        """
        if agent_id:
            messages = [
                msg for msg in self.message_history 
                if msg.get('message', {}).get('to_agent') == agent_id
            ]
        else:
            messages = self.message_history
        # Extract the actual message dict for Message.from_dict (fixes test_message_history)
        return [Message.from_dict(msg['message']) for msg in messages if 'message' in msg]
    
    def clear_history(self, agent_id=None):
        """Clear message history for an agent or all agents.
        
        Args:
            agent_id: Optional agent ID to clear history for
        """
        if not self._acquire_lock():
            return
            
        try:
            if agent_id:
                self.message_history = [
                    msg for msg in self.message_history
                    if msg.get('message', {}).get('to_agent') != agent_id
                ]
                if agent_id in self.message_counts:
                    del self.message_counts[agent_id]
            else:
                self.message_history.clear()
                self.message_counts.clear()
        finally:
            self._release_lock()
            
    def set_test_mode(self, enabled: bool = True):
        """Enable or disable test mode (disables rate limiting).
        
        Args:
            enabled: Whether to enable test mode
        """
        self._is_test_mode = enabled

def load_queue(self) -> List[Dict]:
    """Load queue from disk."""
    return load_json(self.queue_path, default=[])

def save_queue(self, queue: List[Dict]) -> None:
    """Save queue to disk."""
    save_json(self.queue_path, queue)

def load_queue_file(queue_file: str) -> List[Dict]:
    """Load queue from file."""
    return load_json(queue_file)
