"""
Agent Cellphone Module

This module provides communication functionality for agents in Dream.OS.
It handles message passing, notifications, and agent interactions.
"""

from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
import json
from pathlib import Path

from ..state import AgentState
from ..lifecycle import AgentManager

logger = logging.getLogger(__name__)

class AgentCellphone:
    """Handles agent communication and messaging."""
    
    def __init__(self, agent_manager: AgentManager, message_dir: Optional[Path] = None):
        """Initialize agent cellphone.
        
        Args:
            agent_manager: The agent manager instance
            message_dir: Optional directory for message storage
        """
        self.agent_manager = agent_manager
        self.message_dir = message_dir or Path.home() / ".dreamos" / "messages"
        self.message_dir.mkdir(parents=True, exist_ok=True)
        
        self._message_queue: Dict[str, List[Dict[str, Any]]] = {}
        self._notification_queue: Dict[str, List[Dict[str, Any]]] = {}
        
    def send_message(self, from_agent: str, to_agent: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Send a message to another agent.
        
        Args:
            from_agent: Sender agent ID
            to_agent: Recipient agent ID
            content: Message content
            metadata: Optional message metadata
            
        Returns:
            bool: True if message was sent successfully
        """
        try:
            if to_agent not in self.agent_manager.get_agent_ids():
                logger.error(f"Recipient agent {to_agent} not found")
                return False
                
            message = {
                'from': from_agent,
                'to': to_agent,
                'content': content,
                'metadata': metadata or {},
                'timestamp': datetime.now().isoformat()
            }
            
            # Add to queue
            if to_agent not in self._message_queue:
                self._message_queue[to_agent] = []
            self._message_queue[to_agent].append(message)
            
            # Save to file
            self._save_message(message)
            
            logger.info(f"Message sent from {from_agent} to {to_agent}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            return False
            
    def get_messages(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get messages for an agent.
        
        Args:
            agent_id: The agent ID
            
        Returns:
            List[Dict[str, Any]]: List of messages
        """
        try:
            messages = self._message_queue.get(agent_id, [])
            self._message_queue[agent_id] = []  # Clear queue
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get messages for agent {agent_id}: {str(e)}")
            return []
            
    def send_notification(self, to_agent: str, notification_type: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Send a notification to an agent.
        
        Args:
            to_agent: Recipient agent ID
            notification_type: Type of notification
            content: Notification content
            metadata: Optional notification metadata
            
        Returns:
            bool: True if notification was sent successfully
        """
        try:
            if to_agent not in self.agent_manager.get_agent_ids():
                logger.error(f"Recipient agent {to_agent} not found")
                return False
                
            notification = {
                'type': notification_type,
                'to': to_agent,
                'content': content,
                'metadata': metadata or {},
                'timestamp': datetime.now().isoformat()
            }
            
            # Add to queue
            if to_agent not in self._notification_queue:
                self._notification_queue[to_agent] = []
            self._notification_queue[to_agent].append(notification)
            
            # Save to file
            self._save_notification(notification)
            
            logger.info(f"Notification sent to {to_agent}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
            return False
            
    def get_notifications(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get notifications for an agent.
        
        Args:
            agent_id: The agent ID
            
        Returns:
            List[Dict[str, Any]]: List of notifications
        """
        try:
            notifications = self._notification_queue.get(agent_id, [])
            self._notification_queue[agent_id] = []  # Clear queue
            return notifications
            
        except Exception as e:
            logger.error(f"Failed to get notifications for agent {agent_id}: {str(e)}")
            return []
            
    def _save_message(self, message: Dict[str, Any]) -> None:
        """Save a message to file.
        
        Args:
            message: Message to save
        """
        try:
            message_file = self.message_dir / f"message_{message['timestamp']}.json"
            with open(message_file, 'w') as f:
                json.dump(message, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save message: {str(e)}")
            
    def _save_notification(self, notification: Dict[str, Any]) -> None:
        """Save a notification to file.
        
        Args:
            notification: Notification to save
        """
        try:
            notification_file = self.message_dir / f"notification_{notification['timestamp']}.json"
            with open(notification_file, 'w') as f:
                json.dump(notification, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save notification: {str(e)}") 