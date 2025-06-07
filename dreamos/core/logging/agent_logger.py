"""
Agent Logger Module

Provides functionality for agents to update their development logs
and notify Discord of updates.
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger('agent_logger')

class AgentLogger:
    """Handles agent development logging and Discord notifications."""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.log_path = f"runtime/agent_memory/{agent_id}/devlog.md"
        self.inbox_path = f"runtime/agent_memory/{agent_id}/inbox.json"
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        
    def log(self, message: str, category: str = "INFO", metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Log a message to the agent's devlog.
        
        Args:
            message: The log message
            category: Message category (INFO, WARNING, ERROR, etc.)
            metadata: Optional metadata to include
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Format log entry
            timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M]")
            entry = f"{timestamp} [{category}] {message}\n"
            
            # Add metadata if provided
            if metadata:
                entry += f"```json\n{json.dumps(metadata, indent=2)}\n```\n"
                
            # Append to devlog
            with open(self.log_path, "a") as f:
                f.write(entry)
                
            # Create inbox message for Discord notification
            self._create_inbox_message(message, category, metadata)
            return True
            
        except Exception as e:
            logger.error(f"Error logging message: {e}")
            return False
            
    def _create_inbox_message(self, message: str, category: str, metadata: Optional[Dict[str, Any]] = None):
        """Create a message in the agent's inbox for Discord notification."""
        try:
            inbox_message = {
                "type": "DEVLOG_UPDATE",
                "content": message,
                "category": category,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            with open(self.inbox_path, "w") as f:
                json.dump(inbox_message, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error creating inbox message: {e}")
            
    def get_log(self) -> Optional[str]:
        """Get the contents of the agent's devlog."""
        try:
            if not os.path.exists(self.log_path):
                return None
                
            with open(self.log_path, 'r') as f:
                return f.read()
                
        except Exception as e:
            logger.error(f"Error reading devlog: {e}")
            return None
            
    def clear_log(self) -> bool:
        """Clear the agent's devlog with backup."""
        try:
            if not os.path.exists(self.log_path):
                return False
                
            # Create backup
            backup_path = f"{self.log_path}.backup"
            with open(self.log_path, 'r') as src, open(backup_path, 'w') as dst:
                dst.write(src.read())
                
            # Clear the log
            with open(self.log_path, 'w') as f:
                f.write(f"# {self.agent_id} Devlog\n\n")
                f.write(f"Log cleared at {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
                
            return True
            
        except Exception as e:
            logger.error(f"Error clearing devlog: {e}")
            return False 