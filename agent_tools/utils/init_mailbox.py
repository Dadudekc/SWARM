"""
Mailbox Initialization
--------------------
Initialize agent mailboxes.
"""

import os
from pathlib import Path
from typing import Dict, Optional

from dreamos.core.utils.core_utils import (
    safe_read,
    safe_write,
    load_json,
    save_json
)

class AgentMailbox:
    """Agent mailbox for message handling."""
    
    def __init__(self, agent_id: str, base_dir: Optional[str] = None):
        """Initialize agent mailbox.
        
        Args:
            agent_id: Agent identifier
            base_dir: Optional base directory
        """
        self.agent_id = agent_id
        self.base_dir = Path(base_dir or "data/mailboxes")
        self.mailbox_dir = self.base_dir / agent_id
        
        # Create directories
        self.mailbox_dir.mkdir(parents=True, exist_ok=True)
        (self.mailbox_dir / "inbox").mkdir(exist_ok=True)
        (self.mailbox_dir / "outbox").mkdir(exist_ok=True)
        (self.mailbox_dir / "archive").mkdir(exist_ok=True)
    
    def get_inbox(self) -> Dict[str, str]:
        """Get inbox messages.
        
        Returns:
            Dictionary of message IDs to content
        """
        inbox_dir = self.mailbox_dir / "inbox"
        messages = {}
        
        for file_path in inbox_dir.glob("*.json"):
            message = load_json(str(file_path))
            if message:
                messages[file_path.stem] = message
        
        return messages
    
    def get_outbox(self) -> Dict[str, str]:
        """Get outbox messages.
        
        Returns:
            Dictionary of message IDs to content
        """
        outbox_dir = self.mailbox_dir / "outbox"
        messages = {}
        
        for file_path in outbox_dir.glob("*.json"):
            message = load_json(str(file_path))
            if message:
                messages[file_path.stem] = message
        
        return messages
    
    def send_message(self, message_id: str, content: Dict[str, str]) -> bool:
        """Send a message.
        
        Args:
            message_id: Message identifier
            content: Message content
            
        Returns:
            True if successful
        """
        try:
            outbox_dir = self.mailbox_dir / "outbox"
            message_file = outbox_dir / f"{message_id}.json"
            return save_json(str(message_file), content)
        except Exception:
            return False
    
    def receive_message(self, message_id: str, content: Dict[str, str]) -> bool:
        """Receive a message.
        
        Args:
            message_id: Message identifier
            content: Message content
            
        Returns:
            True if successful
        """
        try:
            inbox_dir = self.mailbox_dir / "inbox"
            message_file = inbox_dir / f"{message_id}.json"
            return save_json(str(message_file), content)
        except Exception:
            return False
    
    def archive_message(self, message_id: str, direction: str = "inbox") -> bool:
        """Archive a message.
        
        Args:
            message_id: Message identifier
            direction: Message direction ("inbox" or "outbox")
            
        Returns:
            True if successful
        """
        try:
            source_dir = self.mailbox_dir / direction
            archive_dir = self.mailbox_dir / "archive"
            
            message_file = source_dir / f"{message_id}.json"
            if not message_file.exists():
                return False
            
            # Move to archive
            archive_file = archive_dir / f"{message_id}.json"
            message_file.rename(archive_file)
            return True
        except Exception:
            return False 