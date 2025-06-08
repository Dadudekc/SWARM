"""
Message Handler for Agent Mailbox System

This is a drop-in replacement for the legacy messages/ message handler.
It maintains the same sequential message passing logic but uses the new
mailbox directory structure under data/mailbox/.

Migration Note:
- Old path: messages/{inbox,outbox,processed}/
- New path: data/mailbox/{inbox,outbox,processed}/
- Same API, same sequence tracking, same agent routing rules
"""

import json
import os
import time
import shutil
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class MessageHandler:
    # Valid message modes and priorities
    VALID_MODES = {'sync', 'async', 'broadcast'}
    VALID_PRIORITIES = {'low', 'normal', 'high', 'urgent'}
    
    def __init__(self, base_dir: str = "data/mailbox"):
        """Initialize the message handler.
        
        Args:
            base_dir: Base directory for message storage (defaults to data/mailbox)
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Message handler initialized with base dir: {base_dir}")
        self.inbox_dir = self.base_dir / "inbox"
        self.outbox_dir = self.base_dir / "outbox"
        self.processed_dir = self.base_dir / "processed"
        self.sequence_file = self.base_dir / "sequence.json"
        
        # Ensure directories exist
        for dir_path in [self.inbox_dir, self.outbox_dir, self.processed_dir]:
            dir_path.mkdir(exist_ok=True)
            
        # Initialize sequence if not exists
        if not self.sequence_file.exists():
            self._initialize_sequence()
            
    def _initialize_sequence(self):
        """Initialize the sequence tracking file."""
        sequence_data = {
            "current_sequence": 0,
            "last_agent": None,
            "last_update": None
        }
        with open(self.sequence_file, 'w') as f:
            json.dump(sequence_data, f, indent=4)
            
    def _get_sequence_data(self) -> Dict:
        """Get current sequence data."""
        with open(self.sequence_file, 'r') as f:
            return json.load(f)
            
    def _update_sequence(self, agent_id: str):
        """Update sequence data after message processing."""
        sequence_data = self._get_sequence_data()
        sequence_data["current_sequence"] += 1
        sequence_data["last_agent"] = agent_id
        sequence_data["last_update"] = datetime.utcnow().isoformat()
        
        with open(self.sequence_file, 'w') as f:
            json.dump(sequence_data, f, indent=4)
            
    def get_next_agent(self) -> Optional[str]:
        """Get the next agent in sequence."""
        sequence_data = self._get_sequence_data()
        return sequence_data["last_agent"]
            
    def send_message(
        self,
        to_agent: str,
        content: str,
        from_agent: str,
        metadata: Optional[Dict[str, Any]] = None,
        priority: Optional[str] = None,
        mode: Optional[str] = None
    ) -> bool:
        """Send a message to an agent."""
        if not to_agent or not content or not from_agent:
            logger.error("Invalid message parameters")
            return False
        # Normalize mode/priority for validation
        mode_norm = mode.lower() if mode else None
        priority_norm = priority.lower() if priority else None
        if mode_norm is not None and mode_norm not in self.VALID_MODES:
            logger.error(f"Invalid message mode: {mode}")
            return False
        if priority_norm is not None and priority_norm not in self.VALID_PRIORITIES:
            logger.error(f"Invalid message priority: {priority}")
            return False
        try:
            message = {
                'id': str(uuid.uuid4()),
                'from_agent': from_agent,
                'from': from_agent,  # Alias for compatibility
                'to_agent': to_agent,
                'content': content,
                'timestamp': datetime.now().isoformat(),
                'metadata': metadata or {},
                'priority': priority_norm if priority_norm is not None else 'normal',
                'mode': mode_norm if mode_norm is not None else 'sync',
                'status': 'pending',
                'sequence': self._get_sequence_data()["current_sequence"]
            }
            # Save to agent_dir
            message_dir = self.base_dir / to_agent
            message_dir.mkdir(exist_ok=True)
            message_file = message_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(message_file, 'w') as f:
                json.dump(message, f, indent=2)
            # Save to inbox
            inbox_path = self.inbox_dir / f"msg_{message['sequence']}_{from_agent}_to_{to_agent}.json"
            with open(inbox_path, 'w') as f:
                json.dump(message, f, indent=2)
            self._update_sequence(from_agent)
            return True
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False

    def broadcast_message(
        self,
        content: str,
        from_agent: str,
        metadata: Optional[Dict[str, Any]] = None,
        priority: Optional[str] = None,
        mode: Optional[str] = None
    ) -> bool:
        """Broadcast message to all agents except sender."""
        try:
            agent_dirs = [d for d in self.base_dir.iterdir() if d.is_dir() and d.name not in ['inbox', 'outbox', 'processed']]
            success = True
            for agent_dir in agent_dirs:
                agent_id = agent_dir.name
                if agent_id != from_agent:
                    if not self.send_message(
                        to_agent=agent_id,
                        content=content,
                        from_agent=from_agent,
                        metadata=metadata,
                        priority=priority,
                        mode=mode
                    ):
                        success = False
            return success
        except Exception as e:
            logger.error(f"Error broadcasting message: {e}")
            return False

    def get_messages(self, agent_id: str) -> List[Dict]:
        """Get all messages for an agent from both agent_dir and inbox, deduplicated."""
        try:
            agent_dir = self.base_dir / agent_id
            agent_dir.mkdir(exist_ok=True)
            messages = []
            seen_ids = set()
            # From agent_dir
            for msg_file in agent_dir.glob("*.json"):
                try:
                    with open(msg_file, 'r') as f:
                        message = json.load(f)
                        if message['id'] not in seen_ids:
                            messages.append(message)
                            seen_ids.add(message['id'])
                except json.JSONDecodeError:
                    continue
            # From inbox
            for msg_file in self.inbox_dir.glob(f"*_to_{agent_id}.json"):
                try:
                    with open(msg_file, 'r') as f:
                        message = json.load(f)
                        if message['id'] not in seen_ids:
                            messages.append(message)
                            seen_ids.add(message['id'])
                except json.JSONDecodeError:
                    continue
            messages.sort(key=lambda x: x.get('timestamp', ''))
            return messages
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return []
            
    def mark_as_processed(self, message: Dict):
        """Mark a message as processed.
        
        Args:
            message: Message to mark as processed
        """
        try:
            # Move to processed directory
            processed_path = self.processed_dir / f"msg_{message['sequence']}_{message['from_agent']}_to_{message['to_agent']}.json"
            with open(processed_path, 'w') as f:
                json.dump(message, f, indent=2)
                
            # Remove from inbox
            inbox_path = self.inbox_dir / f"msg_{message['sequence']}_{message['from_agent']}_to_{message['to_agent']}.json"
            if inbox_path.exists():
                inbox_path.unlink()
                
        except Exception as e:
            logger.error(f"Error marking message as processed: {e}")
            
    def cleanup_old_messages(self, max_age_days: int = 7, retry_attempts: int = 3, retry_delay: float = 0.1):
        """Clean up old messages.
        
        Args:
            max_age_days: Maximum age of messages in days
            retry_attempts: Number of retry attempts for failed deletions
            retry_delay: Delay between retries in seconds
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            
            # Clean up processed messages
            for msg_file in self.processed_dir.glob("*.json"):
                try:
                    with open(msg_file, 'r') as f:
                        message = json.load(f)
                        msg_date = datetime.fromisoformat(message['timestamp'])
                        if msg_date < cutoff_date:
                            for attempt in range(retry_attempts):
                                try:
                                    msg_file.unlink()
                                    break
                                except Exception:
                                    if attempt < retry_attempts - 1:
                                        time.sleep(retry_delay)
                                    else:
                                        logger.error(f"Failed to delete old message after {retry_attempts} attempts: {msg_file}")
                except json.JSONDecodeError:
                    logger.error(f"Error decoding message file: {msg_file}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error cleaning up old messages: {e}")
            
    def acknowledge_message(self, message_id: str) -> bool:
        """Acknowledge receipt of a message and remove from inbox and agent_dir."""
        try:
            found = False
            # Remove from inbox
            for msg_file in self.inbox_dir.glob("*.json"):
                try:
                    with open(msg_file, 'r') as f:
                        message = json.load(f)
                        if message.get('id') == message_id:
                            message['status'] = 'acknowledged'
                            with open(msg_file, 'w') as f2:
                                json.dump(message, f2, indent=2)
                            msg_file.unlink()
                            found = True
                            break
                except json.JSONDecodeError:
                    continue
            # Remove from agent_dir
            for agent_dir in self.base_dir.iterdir():
                if agent_dir.is_dir() and agent_dir.name not in ['inbox', 'outbox', 'processed']:
                    for msg_file in agent_dir.glob("*.json"):
                        try:
                            with open(msg_file, 'r') as f:
                                message = json.load(f)
                                if message.get('id') == message_id:
                                    msg_file.unlink()
                                    found = True
                                    break
                        except json.JSONDecodeError:
                            continue
            return found
        except Exception as e:
            logger.error(f"Error acknowledging message: {e}")
            return False

    def save_response(self, agent_id: str, response: Dict[str, Any]) -> bool:
        """Save an agent's response to a message, with a 'response' field."""
        try:
            message = {
                'id': str(uuid.uuid4()),
                'from_agent': agent_id,
                'from': agent_id,  # Alias for compatibility
                'to_agent': response.get('to_agent', 'captain'),
                'content': response.get('content', ''),
                'timestamp': datetime.now().isoformat(),
                'metadata': response.get('metadata', {}),
                'priority': response.get('priority', 'normal'),
                'mode': response.get('mode', 'sync'),
                'status': 'response',
                'sequence': self._get_sequence_data()["current_sequence"],
                'response': response  # Store the full response
            }
            response_dir = self.base_dir / 'responses'
            response_dir.mkdir(exist_ok=True)
            response_file = response_dir / f"response_{message['id']}.json"
            with open(response_file, 'w') as f:
                json.dump(message, f, indent=2)
            self._update_sequence(agent_id)
            return True
        except Exception as e:
            logger.error(f"Error saving response: {e}")
            return False

    def clear_messages(self, agent_id: Optional[str] = None) -> bool:
        """Clear all messages for an agent or all agents.
        
        Args:
            agent_id: Optional agent ID to clear messages for. If None, clears all messages.
            
        Returns:
            bool: True if messages cleared successfully
        """
        try:
            if agent_id:
                # Clear messages for specific agent
                agent_dir = self.base_dir / agent_id
                if agent_dir.exists():
                    for msg_file in agent_dir.glob("*.json"):
                        msg_file.unlink()
            else:
                # Clear all messages
                for dir_path in [self.inbox_dir, self.outbox_dir, self.processed_dir]:
                    for msg_file in dir_path.glob("*.json"):
                        msg_file.unlink()
                        
                # Clear agent directories
                for agent_dir in self.base_dir.iterdir():
                    if agent_dir.is_dir() and agent_dir.name not in ['inbox', 'outbox', 'processed']:
                        for msg_file in agent_dir.glob("*.json"):
                            msg_file.unlink()
                            
            return True
            
        except Exception as e:
            logger.error(f"Error clearing messages: {e}")
            return False
            
    def update_message_status(self, message_id: str, status: str) -> bool:
        """Update the status of a message (e.g., to 'timeout')."""
        try:
            for msg_file in self.inbox_dir.glob("*.json"):
                try:
                    with open(msg_file, 'r') as f:
                        message = json.load(f)
                        if message.get('id') == message_id:
                            message['status'] = status
                            with open(msg_file, 'w') as f2:
                                json.dump(message, f2, indent=2)
                            return True
                except json.JSONDecodeError:
                    continue
            return False
        except Exception as e:
            logger.error(f"Error updating message status: {e}")
            return False 
