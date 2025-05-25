"""
Queue Module

Handles message queuing and persistence for the Dream.OS messaging system.
"""

import logging
import json
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
from queue import PriorityQueue
from datetime import datetime

from .message import Message

logger = logging.getLogger('messaging.queue')

class MessageQueue:
    """Manages message queuing and persistence."""
    
    def __init__(self, queue_path: Optional[str] = None):
        """Initialize the message queue.
        
        Args:
            queue_path: Optional path to queue storage file
        """
        self._queue = PriorityQueue()
        self._history: List[Dict[str, Any]] = []
        self._max_history = 1000
        self._lock = threading.Lock()
        
        # Set up queue storage
        if queue_path:
            self.queue_path = Path(queue_path)
            self.queue_path.parent.mkdir(parents=True, exist_ok=True)
            self._load_queue()
        else:
            self.queue_path = None
            
    def enqueue(self, message: Message) -> bool:
        """Add a message to the queue.
        
        Args:
            message: Message to add
            
        Returns:
            bool: True if message was successfully queued
        """
        try:
            if not message.validate():
                return False
                
            # Calculate priority (higher number = higher priority)
            priority = message.priority
            timestamp = datetime.now().timestamp()
            
            # Add to queue
            self._queue.put((-priority, timestamp, message.to_dict()))
            
            # Add to history
            with self._lock:
                self._history.append({
                    'message': message.to_dict(),
                    'timestamp': timestamp,
                    'status': 'queued'
                })
                
                # Trim history if needed
                if len(self._history) > self._max_history:
                    self._history = self._history[-self._max_history:]
                    
            # Save queue if path is set
            if self.queue_path:
                self._save_queue()
                
            logger.info(f"Message queued from {message.from_agent} to {message.to_agent}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enqueue message: {e}")
            return False
            
    def dequeue(self) -> Optional[Dict[str, Any]]:
        """Get next message from queue.
        
        Returns:
            Optional[Dict]: Next message or None if queue is empty
        """
        try:
            if self._queue.empty():
                return None
                
            _, _, message = self._queue.get()
            
            # Update history
            with self._lock:
                for hist_msg in self._history:
                    if hist_msg['message'] == message:
                        hist_msg['status'] = 'processing'
                        hist_msg['processing_time'] = datetime.now().timestamp()
                        break
                        
            # Save queue if path is set
            if self.queue_path:
                self._save_queue()
                
            return message
            
        except Exception as e:
            logger.error(f"Failed to dequeue message: {e}")
            return None
            
    def get_status(self) -> Dict[str, Any]:
        """Get current queue status.
        
        Returns:
            Dict containing queue statistics
        """
        try:
            return {
                'queue_size': self._queue.qsize(),
                'history_size': len(self._history),
                'recent_messages': self._history[-10:] if self._history else []
            }
        except Exception as e:
            logger.error(f"Failed to get queue status: {e}")
            return {'error': str(e)}
            
    def clear(self, agent_id: Optional[str] = None) -> None:
        """Clear messages from queue.
        
        Args:
            agent_id: Optional agent ID to clear messages for
        """
        try:
            if agent_id:
                # Create new queue without agent's messages
                new_queue = PriorityQueue()
                while not self._queue.empty():
                    priority, timestamp, message = self._queue.get()
                    if message['to_agent'] != agent_id:
                        new_queue.put((priority, timestamp, message))
                self._queue = new_queue
                
                # Update history
                with self._lock:
                    self._history = [
                        msg for msg in self._history 
                        if msg['message']['to_agent'] != agent_id
                    ]
            else:
                # Clear entire queue
                while not self._queue.empty():
                    self._queue.get()
                with self._lock:
                    self._history = []
                    
            # Save queue if path is set
            if self.queue_path:
                self._save_queue()
                
            logger.info(f"Queue cleared for {agent_id if agent_id else 'all agents'}")
            
        except Exception as e:
            logger.error(f"Failed to clear queue: {e}")
            
    def _save_queue(self) -> None:
        """Save queue to file."""
        try:
            # Convert queue to list
            queue_list = []
            while not self._queue.empty():
                priority, timestamp, message = self._queue.get()
                queue_list.append({
                    'priority': -priority,  # Convert back to positive
                    'timestamp': timestamp,
                    'message': message
                })
                
            # Save to file
            with open(self.queue_path, 'w') as f:
                json.dump({
                    'queue': queue_list,
                    'history': self._history
                }, f, indent=2)
                
            # Restore queue
            for item in queue_list:
                self._queue.put((-item['priority'], item['timestamp'], item['message']))
                
        except Exception as e:
            logger.error(f"Failed to save queue: {e}")
            
    def _load_queue(self) -> None:
        """Load queue from file."""
        try:
            if not self.queue_path.exists():
                return
                
            # Load from file
            with open(self.queue_path, 'r') as f:
                data = json.load(f)
                
            # Restore queue
            for item in data['queue']:
                self._queue.put((-item['priority'], item['timestamp'], item['message']))
                
            # Restore history
            with self._lock:
                self._history = data['history']
                
        except Exception as e:
            logger.error(f"Failed to load queue: {e}")
            
    def shutdown(self) -> None:
        """Clean up resources."""
        try:
            if self.queue_path:
                self._save_queue()
            logger.info("Message queue shut down")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}") 