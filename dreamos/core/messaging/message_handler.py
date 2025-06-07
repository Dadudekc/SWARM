"""
Message Handler
--------------
Manages message routing and delivery between agents with security validation.
"""

import json
import logging
import os
import re
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List, Any, Tuple

logger = logging.getLogger(__name__)

class MessageValidationError(Exception):
    """Raised when message validation fails."""
    pass

class MessageHandler:
    """Handles message routing and delivery between agents with security validation."""
    
    # Constants
    MAX_MESSAGE_SIZE = 1024 * 1024  # 1MB
    MAX_FILENAME_LENGTH = 255
    ALLOWED_AGENT_CHARS = re.compile(r'^[a-zA-Z0-9_-]+$')
    ALLOWED_MESSAGE_MODES = {'NORMAL', 'PRIORITY', 'SYSTEM'}
    
    def __init__(self, base_dir: str):
        """Initialize the message handler.
        
        Args:
            base_dir: Base directory for message storage
        """
        self.base_dir = Path(base_dir)
        self.inbox_dir = self.base_dir / "inbox"
        self.outbox_dir = self.base_dir / "outbox"
        self.processed_dir = self.base_dir / "processed"
        self.corrupted_dir = self.base_dir / "corrupted"
        self.agent_status_file = self.base_dir / "agent_status.json"
        
        # Create directories
        for dir_path in [self.inbox_dir, self.outbox_dir, self.processed_dir, self.corrupted_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize agent status tracking
        self._init_agent_status()
        
        logger.info(f"Message handler initialized with base directory: {base_dir}")
    
    def _init_agent_status(self) -> None:
        """Initialize agent status tracking."""
        if not self.agent_status_file.exists():
            self._save_agent_status({})
    
    def _save_agent_status(self, status: Dict) -> None:
        """Save agent status to file."""
        try:
            with self.agent_status_file.open('w') as f:
                json.dump(status, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving agent status: {e}")
    
    def _load_agent_status(self) -> Dict:
        """Load agent status from file."""
        try:
            if self.agent_status_file.exists():
                with self.agent_status_file.open() as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading agent status: {e}")
            return {}
    
    def is_valid_message(self, message: Dict) -> Tuple[bool, str]:
        """Validate message structure and content.
        
        Args:
            message: Message to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check basic structure
            if not isinstance(message, dict):
                return False, "Message must be a dictionary"
            
            # Check required fields
            required_fields = {'from', 'to', 'content', 'mode', 'timestamp'}
            missing_fields = required_fields - set(message.keys())
            if missing_fields:
                return False, f"Missing required fields: {missing_fields}"
            
            # Validate agent IDs
            if not self.ALLOWED_AGENT_CHARS.match(message['from']):
                return False, f"Invalid 'from' agent ID: {message['from']}"
            if not self.ALLOWED_AGENT_CHARS.match(message['to']):
                return False, f"Invalid 'to' agent ID: {message['to']}"
            
            # Validate message mode
            if message['mode'] not in self.ALLOWED_MESSAGE_MODES:
                return False, f"Invalid message mode: {message['mode']}"
            
            # Validate timestamp
            if not isinstance(message['timestamp'], (int, float)):
                return False, "Timestamp must be numeric"
            
            # Validate content
            if not isinstance(message['content'], str):
                return False, "Content must be a string"
            if len(message['content']) > self.MAX_MESSAGE_SIZE:
                return False, f"Content exceeds maximum size of {self.MAX_MESSAGE_SIZE} bytes"
            
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal.
        
        Args:
            filename: Filename to sanitize
            
        Returns:
            Sanitized filename
        """
        # Remove path components
        filename = os.path.basename(filename)
        
        # Remove invalid characters
        filename = re.sub(r'[^\w\-_.]', '_', filename)
        
        # Truncate if too long
        if len(filename) > self.MAX_FILENAME_LENGTH:
            filename = filename[:self.MAX_FILENAME_LENGTH]
        
        return filename
    
    def handle_corrupted_inbox(self, agent_id: str) -> None:
        """Handle corrupted inbox for an agent.
        
        Args:
            agent_id: Agent ID with corrupted inbox
        """
        try:
            # Update agent status
            status = self._load_agent_status()
            status[agent_id] = {
                'status': 'ERROR',
                'last_error': 'Corrupted inbox detected',
                'timestamp': time.time()
            }
            self._save_agent_status(status)
            
            # Move corrupted inbox
            inbox_file = self.inbox_dir / f"{agent_id}.json"
            if inbox_file.exists():
                corrupted_file = self.corrupted_dir / f"{agent_id}_{int(time.time())}.json"
                shutil.move(str(inbox_file), str(corrupted_file))
                logger.warning(f"Moved corrupted inbox for {agent_id} to {corrupted_file}")
            
        except Exception as e:
            logger.error(f"Error handling corrupted inbox for {agent_id}: {e}")
    
    def send_message(self, from_agent: str, to_agent: str, content: str, mode: str = "NORMAL") -> bool:
        """Send a message from one agent to another.
        
        Args:
            from_agent: Source agent ID
            to_agent: Target agent ID
            content: Message content
            mode: Message mode (NORMAL, PRIORITY, etc.)
            
        Returns:
            bool: True if message was sent successfully
        """
        try:
            # Create message
            message = {
                "from": from_agent,
                "to": to_agent,
                "content": content,
                "mode": mode,
                "timestamp": time.time()
            }
            
            # Validate message
            is_valid, error_msg = self.is_valid_message(message)
            if not is_valid:
                logger.error(f"Invalid message: {error_msg}")
                return False
            
            # Sanitize filenames
            outbox_filename = self.sanitize_filename(f"{from_agent}_to_{to_agent}.json")
            inbox_filename = self.sanitize_filename(f"{to_agent}.json")
            
            # Save to outbox
            outbox_file = self.outbox_dir / outbox_filename
            with outbox_file.open("w") as f:
                json.dump(message, f, indent=2)
            
            # Save to recipient's inbox
            inbox_file = self.inbox_dir / inbox_filename
            with inbox_file.open("w") as f:
                json.dump(message, f, indent=2)
            
            logger.info(f"Message sent from {from_agent} to {to_agent}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def get_messages(self, agent_id: str) -> List[Dict]:
        """Get all messages for an agent.
        
        Args:
            agent_id: Agent ID to get messages for
            
        Returns:
            List of messages
        """
        try:
            inbox_file = self.inbox_dir / f"{agent_id}.json"
            if not inbox_file.exists():
                return []
            
            # Check for corruption
            try:
                with inbox_file.open() as f:
                    messages = json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Corrupted inbox detected for {agent_id}")
                self.handle_corrupted_inbox(agent_id)
                return []
            
            # Validate each message
            valid_messages = []
            for msg in messages:
                is_valid, error_msg = self.is_valid_message(msg)
                if is_valid:
                    valid_messages.append(msg)
                else:
                    logger.warning(f"Invalid message in inbox for {agent_id}: {error_msg}")
            
            return valid_messages
                
        except Exception as e:
            logger.error(f"Error getting messages for {agent_id}: {e}")
            return []
    
    def mark_as_processed(self, agent_id: str, message_id: str) -> bool:
        """Mark a message as processed.
        
        Args:
            agent_id: Agent ID
            message_id: Message ID to mark as processed
            
        Returns:
            bool: True if message was marked as processed
        """
        try:
            # Move from inbox to processed
            inbox_file = self.inbox_dir / f"{agent_id}.json"
            processed_file = self.processed_dir / f"{agent_id}_{message_id}.json"
            
            if inbox_file.exists():
                inbox_file.rename(processed_file)
                logger.info(f"Message {message_id} marked as processed for {agent_id}")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error marking message as processed: {e}")
            return False
    
    def cleanup_old_messages(self, max_age_days: int = 7) -> None:
        """Clean up old processed messages.
        
        Args:
            max_age_days: Maximum age of messages to keep
        """
        try:
            cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
            
            for dir_path in [self.processed_dir, self.corrupted_dir]:
                for file in dir_path.glob("*.json"):
                    if file.stat().st_mtime < cutoff_time:
                        file.unlink()
                        logger.info(f"Cleaned up old message: {file}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up old messages: {e}")
    
    def get_agent_status(self, agent_id: str) -> Dict:
        """Get status for a specific agent.
        
        Args:
            agent_id: Agent ID to get status for
            
        Returns:
            Agent status dictionary
        """
        status = self._load_agent_status()
        return status.get(agent_id, {
            'status': 'UNKNOWN',
            'last_error': None,
            'timestamp': None
        })
    
    def update_agent_status(self, agent_id: str, status: str, error: Optional[str] = None) -> None:
        """Update status for a specific agent.
        
        Args:
            agent_id: Agent ID to update
            status: New status
            error: Optional error message
        """
        try:
            current_status = self._load_agent_status()
            current_status[agent_id] = {
                'status': status,
                'last_error': error,
                'timestamp': time.time()
            }
            self._save_agent_status(current_status)
            logger.info(f"Updated status for {agent_id}: {status}")
        except Exception as e:
            logger.error(f"Error updating agent status: {e}") 