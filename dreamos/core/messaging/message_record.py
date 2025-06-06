"""Message record tracking and persistence."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class MessageRecord:
    """Tracks message history and persistence."""
    
    def __init__(self, record_dir: str):
        """Initialize message record tracking.
        
        Args:
            record_dir: Directory to store message records
        """
        self.record_dir = Path(record_dir)
        self.record_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def record_message(self, message: Dict) -> bool:
        """Record a message in history.
        
        Args:
            message: Message dictionary to record
            
        Returns:
            bool: True if message was recorded successfully
        """
        try:
            # Create timestamp-based filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"message_{timestamp}.json"
            filepath = self.record_dir / filename
            
            # Add record timestamp
            message['recorded_at'] = datetime.now().isoformat()
            
            # Save message
            with open(filepath, 'w') as f:
                json.dump(message, f, indent=2)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error recording message: {e}")
            return False
    
    def get_history(self, agent_id: Optional[str] = None) -> List[Dict]:
        """Get message history.
        
        Args:
            agent_id: Optional agent ID to filter history
            
        Returns:
            List[Dict]: List of recorded messages
        """
        try:
            messages = []
            for filepath in self.record_dir.glob("message_*.json"):
                try:
                    with open(filepath, 'r') as f:
                        message = json.load(f)
                        if agent_id is None or message.get('recipient') == agent_id:
                            messages.append(message)
                except json.JSONDecodeError:
                    self.logger.warning(f"Invalid JSON in {filepath}")
                    continue
            
            # Sort by recorded timestamp
            messages.sort(key=lambda x: x.get('recorded_at', ''))
            return messages
            
        except Exception as e:
            self.logger.error(f"Error getting message history: {e}")
            return []
    
    def clear_history(self, agent_id: Optional[str] = None) -> bool:
        """Clear message history.
        
        Args:
            agent_id: Optional agent ID to filter which messages to clear
            
        Returns:
            bool: True if history was cleared successfully
        """
        try:
            if agent_id is None:
                # Clear all messages
                for filepath in self.record_dir.glob("message_*.json"):
                    filepath.unlink()
            else:
                # Clear only messages for specific agent
                for filepath in self.record_dir.glob("message_*.json"):
                    try:
                        with open(filepath, 'r') as f:
                            message = json.load(f)
                            if message.get('recipient') == agent_id:
                                filepath.unlink()
                    except json.JSONDecodeError:
                        continue
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error clearing message history: {e}")
            return False 